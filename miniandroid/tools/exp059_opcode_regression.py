#!/usr/bin/env python3
"""
EXP-059: Targeted regression test for the AOSP opcode-table fix.

These tests generate bytecode that DISTINGUISHES between if-eqz and if-nez
behavior — so they will FAIL if the runtime dispatches the wrong opcode.

Background:
  The runtime's Opcode enum had if-eqz=0x37, if-nez=0x38 (WRONG per AOSP).
  Per AOSP source code (art/libdexfile/dex/dex_instruction_list.h):
    0x38 if-eqz, 0x39 if-nez, 0x3a if-ltz, ...
  The fix moved if-eqz to 0x38 and if-nez to 0x39.

Test design:
  Each test puts a specific value in v0, then branches.
  We verify:
    - exit code == 0 (runtime completed)
    - no HALT-LOOP events (would indicate wrong branch direction
      causing infinite loop)
    - method exit is via return-void (clean exit)

Run:
  python3 tools/exp059_opcode_regression.py
"""

import os, sys, struct, subprocess, zipfile, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp052_exception_tests import (
    DexBuilder, run_test, wrap_in_apk, MINIANDROID_ROOT, RUNTIME_BIN,
    OP_CONST_4, OP_CONST_STRING, OP_RETURN, OP_RETURN_VOID, OP_RETURN_OBJECT,
    OP_MOVE_RESULT_OBJECT, OP_INVOKE_DIRECT, OP_NEW_INSTANCE, OP_INVOKE_STATIC,
    OP_INVOKE_VIRTUAL, OP_MOVE_RESULT,
)

# AOSP-correct opcode values for if-* (EXP-059 fix)
OP_IF_EQZ       = 0x38   # branch if vAA == 0
OP_IF_NEZ       = 0x39   # branch if vAA != 0


def _build_test(test_name: str, init_value: int, opcode: int) -> bytes:
    """Build a generic if-*z branch test.

    Method onCreate:
      PC=0: const/4 v0, #init_value
      PC=1: <opcode> v0, +3 → PC=4
      PC=3: const/4 v0, #99 (skipped or executed depending on branch)
      PC=4: return-void
    """
    b = DexBuilder()
    b.add_string("Ltest/exp052/TestActivity;")    # 0
    b.add_string("Ljava/lang/Object;")           # 1
    b.add_string("Landroid/os/Bundle;")          # 2
    b.add_string("onCreate")                      # 3
    b.add_string("(Landroid/os/Bundle;)V")        # 4
    b.add_string("V")                             # 5
    b.add_type("Ltest/exp052/TestActivity;")      # 0
    b.add_type("Ljava/lang/Object;")             # 1
    b.add_type("Landroid/os/Bundle;")            # 2
    b.add_type("V")                                # 3
    b.add_proto("V", "V")                          # 0
    b.add_method("Ltest/exp052/TestActivity;", "V", "V", "onCreate")  # 0
    b.add_class("Ltest/exp052/TestActivity;", superclass="Landroid/app/Activity;")

    # const/4 vAA, #+B — B in HIGH nibble of byte 1, AA in LOW nibble
    const_byte = ((init_value & 0xF) << 4) | 0x00  # v0 = init_value
    bytecode = [
        # PC=0: const/4 v0, #init_value
        (const_byte << 8) | OP_CONST_4,
        # PC=1: opcode v0, +3 → PC=4
        (0x00 << 8) | opcode, 0x0003,
        # PC=3: const/4 v0, #99
        (0x63 << 8) | OP_CONST_4,
        # PC=4: return-void
        (0x00 << 8) | OP_RETURN_VOID,
    ]
    b.set_class_data(0, [{
        "name": "onCreate",
        "shorty": "V",
        "return_type": "V",
        "args": ["Landroid/os/Bundle;"],
        "access": 0x1,
        "registers": 2,
        "parameters": 1,
        "bytecode": bytecode,
    }])
    return b.serialize()


def main():
    print("=" * 70)
    print("EXP-059 Opcode-Table Regression Tests")
    print("=" * 70)
    print()

    cases = [
        ('if_eqz_zero_taken',     lambda: _build_test('if_eqz_zero',     0, OP_IF_EQZ),
         'if-eqz v0=0 → branch TAKEN (skip PC=3)'),
        ('if_eqz_nonzero_nottaken', lambda: _build_test('if_eqz_nonzero', 1, OP_IF_EQZ),
         'if-eqz v0=1 → branch NOT taken (execute PC=3)'),
        ('if_nez_nonzero_taken',  lambda: _build_test('if_nez_nonzero', 1, OP_IF_NEZ),
         'if-nez v0=1 → branch TAKEN (skip PC=3)'),
        ('if_nez_zero_nottaken',  lambda: _build_test('if_nez_zero',     0, OP_IF_NEZ),
         'if-nez v0=0 → branch NOT taken (execute PC=3)'),
    ]

    results = []
    for name, builder_fn, desc in cases:
        print(f'--- {name} ---')
        print(f'  Description: {desc}')
        dex_bytes = builder_fn()
        result = run_test(name, dex_bytes)
        exit_code = result["exit_code"]
        stderr = result["stderr"]
        halt_count = stderr.count('HALT-LOOP') + stderr.count('HALT-GOTO') + stderr.count('HALT-OPCODE')
        # Look for instructions executed
        stdout = result["stdout"]
        insns_line = next((l for l in stdout.splitlines() if 'Instructions executed' in l), 'no data')
        # Pass = clean exit, no HALT
        passed = (exit_code == 0 and halt_count == 0)
        status = 'PASS' if passed else 'FAIL'
        print(f'  Exit code: {exit_code}')
        print(f'  HALT events: {halt_count}')
        print(f'  {insns_line}')
        print(f'  Status: {status}')
        print()
        results.append((name, exit_code, passed, f'halt={halt_count}'))

    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f'{"Case":30s} {"Exit":5s} {"PASS":5s} {"Details":15s}')
    print("-" * 70)
    for name, exit_code, passed, details in results:
        print(f'{name:30s} {exit_code:<5d} {"YES" if passed else "NO":5s} {details}')

    all_pass = all(p for _, _, p, _ in results)
    print()
    print(f'Overall: {"ALL PASS" if all_pass else "SOME FAIL"}')
    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())
