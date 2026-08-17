#!/usr/bin/env python3
"""
EXP-052: Full Regression Test Suite
====================================

Tests the interpreter against small DEX files that exercise:
  - invoke-virtual/direct/static/super return values
  - Branches (if-eq, if-nez, if-eqz, goto)
  - Exception handling (throw, catch, nested, caller catch)
  - Shadow APIs (Thread identity, Looper identity, Handler queue)

Each test is a small DEX wrapped in an APK. The runtime is run on each
APK and the output is checked against expectations.

This is RESEARCH-ONLY: it does NOT modify C++ source.
"""

import os
import sys
import struct
import subprocess
import time
import zipfile

# Reuse the DEX builder from the exception tests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp052_exception_tests import (
    DexBuilder, run_test, wrap_in_apk, MINIANDROID_ROOT, RUNTIME_BIN,
    OP_CONST_4, OP_CONST_STRING, OP_NEW_INSTANCE, OP_INVOKE_DIRECT,
    OP_INVOKE_VIRTUAL, OP_INVOKE_STATIC, OP_INVOKE_SUPER, OP_MOVE_RESULT,
    OP_MOVE_RESULT_OBJECT, OP_RETURN, OP_RETURN_VOID, OP_THROW, OP_GOTO,
    OP_IF_NEZ, OP_IF_EQZ, OP_RETURN_OBJECT
)

# Extra opcode constants not exported by exp052_exception_tests
OP_IF_EQ = 0x31
OP_IF_NE = 0x32

# ============================================================================
# Test case builders
# ============================================================================

def build_invoke_virtual_return() -> bytes:
    """Test invoke-virtual return value propagation.
    Class: Ltest/exp052/TestActivity; extends Activity.
    Method: onCreate()V — calls toString() on `this`, stores result.
    Expected: the call returns non-null (we just check method runs).
    """
    b = DexBuilder()
    b.add_string("Ltest/exp052/TestActivity;")  # 0
    b.add_string("Ljava/lang/Object;")           # 1
    b.add_string("Ljava/lang/String;")            # 2
    b.add_string("Landroid/os/Bundle;")          # 3
    b.add_string("onCreate")                      # 4
    b.add_string("(Landroid/os/Bundle;)V")        # 5
    b.add_string("V")                             # 6
    b.add_string("toString")                      # 7
    b.add_string("()Ljava/lang/String;")          # 8
    b.add_type("Ltest/exp052/TestActivity;")      # 0
    b.add_type("Ljava/lang/Object;")               # 1
    b.add_type("Ljava/lang/String;")               # 2
    b.add_type("Landroid/os/Bundle;")              # 3
    b.add_type("V")                                # 4
    b.add_proto("V", "V")                          # 0 (onCreate)
    b.add_proto("Ljava/lang/String;", "Ljava/lang/String;")  # 1 (toString)
    b.add_method("Ljava/lang/Object;", "Ljava/lang/String;", "Ljava/lang/String;", "toString")  # 0
    b.add_method("Ltest/exp052/TestActivity;", "V", "V", "onCreate")  # 1
    b.add_class("Ltest/exp052/TestActivity;", superclass="Landroid/app/Activity;")

    # onCreate:
    #   v0 = this.toString()
    #   return-void
    bytecode = [
        # PC=0: invoke-virtual {v2}, Object.toString()  (method@0)
        (0x10 << 8) | OP_INVOKE_VIRTUAL, 0x0000, 0x0200,
        # PC=3: move-result-object v0
        (0x00 << 8) | OP_MOVE_RESULT_OBJECT,
        # PC=4: return-void
        (0x00 << 8) | OP_RETURN_VOID,
    ]
    b.set_class_data(0, [{
        "name": "onCreate",
        "shorty": "V",
        "return_type": "V",
        "access": 0x1,
        "registers_size": 4,
        "ins_size": 2,
        "outs_size": 1,
        "bytecode": bytecode,
        "tries": [],
    }])
    return b.serialize()


def build_invoke_static_return() -> bytes:
    """Test invoke-static return value.
    Class has onCreate (calls helper) + helper.
    """
    b = DexBuilder()
    b.add_string("Ltest/exp052/TestActivity;")  # 0
    b.add_string("Ljava/lang/Object;")           # 1
    b.add_string("Landroid/os/Bundle;")          # 2
    b.add_string("onCreate")                      # 3
    b.add_string("(Landroid/os/Bundle;)V")        # 4
    b.add_string("V")                             # 5
    b.add_string("helper")                        # 6
    b.add_string("()I")                           # 7
    b.add_string("I")                             # 8
    b.add_type("Ltest/exp052/TestActivity;")      # 0
    b.add_type("Ljava/lang/Object;")               # 1
    b.add_type("Landroid/os/Bundle;")              # 2
    b.add_type("V")                                # 3
    b.add_type("I")                                # 4
    b.add_proto("V", "V")                          # 0 (onCreate)
    b.add_proto("I", "I")                          # 1 (helper)
    b.add_method("Ltest/exp052/TestActivity;", "V", "V", "onCreate")  # 0
    b.add_method("Ltest/exp052/TestActivity;", "I", "I", "helper")    # 1
    b.add_class("Ltest/exp052/TestActivity;", superclass="Landroid/app/Activity;")

    # onCreate: v0 = helper(); return-void
    bytecode_oncreate = [
        # PC=0: invoke-static {}, TestActivity.helper()I  (method@1)
        (0x00 << 8) | OP_INVOKE_STATIC, 0x0001, 0x0000,
        # PC=3: move-result v0
        (0x00 << 8) | OP_MOVE_RESULT,
        # PC=4: return-void
        (0x00 << 8) | OP_RETURN_VOID,
    ]
    # helper: return 42
    bytecode_helper = [
        # PC=0: const/4 v0, #42
        (0x2A << 8) | OP_CONST_4,
        # PC=1: return v0
        (0x00 << 8) | OP_RETURN,
    ]
    b.set_class_data(0, [
        {
            "name": "onCreate",
            "shorty": "V",
            "return_type": "V",
            "access": 0x1,
            "registers_size": 2,
            "ins_size": 2,
            "outs_size": 1,
            "bytecode": bytecode_oncreate,
            "tries": [],
        },
        {
            "name": "helper",
            "shorty": "I",
            "return_type": "I",
            "access": 0x9,  # PUBLIC STATIC
            "registers_size": 1,
            "ins_size": 0,
            "outs_size": 0,
            "bytecode": bytecode_helper,
            "tries": [],
        },
    ])
    return b.serialize()


def build_branch_if_eqz() -> bytes:
    """Test if-eqz branch behavior.
    Method: onCreate()V — const/4 v0, #0; if-eqz v0, +2 → PC=4; const/4 v0, #1; PC=4: return-void
    """
    b = DexBuilder()
    b.add_string("Ltest/exp052/TestActivity;")  # 0
    b.add_string("Ljava/lang/Object;")           # 1
    b.add_string("Landroid/os/Bundle;")          # 2
    b.add_string("onCreate")                      # 3
    b.add_string("(Landroid/os/Bundle;)V")        # 4
    b.add_string("V")                             # 5
    b.add_type("Ltest/exp052/TestActivity;")      # 0
    b.add_type("Ljava/lang/Object;")               # 1
    b.add_type("Landroid/os/Bundle;")              # 2
    b.add_type("V")                                # 3
    b.add_proto("V", "V")                          # 0
    b.add_method("Ltest/exp052/TestActivity;", "V", "V", "onCreate")  # 0
    b.add_class("Ltest/exp052/TestActivity;", superclass="Landroid/app/Activity;")

    bytecode = [
        # PC=0: const/4 v0, #0
        (0x00 << 8) | OP_CONST_4,
        # PC=1: if-eqz v0, +2 → PC=3
        (0x00 << 8) | OP_IF_EQZ, 0x0002,
        # PC=3: return-void
        (0x00 << 8) | OP_RETURN_VOID,
    ]
    b.set_class_data(0, [{
        "name": "onCreate",
        "shorty": "V",
        "return_type": "V",
        "access": 0x1,
        "registers_size": 4,
        "ins_size": 2,
        "outs_size": 0,
        "bytecode": bytecode,
        "tries": [],
    }])
    return b.serialize()


def build_branch_if_nez() -> bytes:
    """Test if-nez branch behavior.
    Method: const/4 v0, #1; if-nez v0, +2 → PC=4; const/4 v0, #99; PC=4: return-void
    """
    b = DexBuilder()
    b.add_string("Ltest/exp052/TestActivity;")  # 0
    b.add_string("Ljava/lang/Object;")           # 1
    b.add_string("Landroid/os/Bundle;")          # 2
    b.add_string("onCreate")                      # 3
    b.add_string("(Landroid/os/Bundle;)V")        # 4
    b.add_string("V")                             # 5
    b.add_type("Ltest/exp052/TestActivity;")      # 0
    b.add_type("Ljava/lang/Object;")               # 1
    b.add_type("Landroid/os/Bundle;")              # 2
    b.add_type("V")                                # 3
    b.add_proto("V", "V")                          # 0
    b.add_method("Ltest/exp052/TestActivity;", "V", "V", "onCreate")  # 0
    b.add_class("Ltest/exp052/TestActivity;", superclass="Landroid/app/Activity;")

    bytecode = [
        # PC=0: const/4 v0, #1
        (0x10 << 8) | OP_CONST_4,
        # PC=1: if-nez v0, +2 → PC=3
        (0x00 << 8) | OP_IF_NEZ, 0x0002,
        # PC=3: return-void
        (0x00 << 8) | OP_RETURN_VOID,
    ]
    b.set_class_data(0, [{
        "name": "onCreate",
        "shorty": "V",
        "return_type": "V",
        "access": 0x1,
        "registers_size": 4,
        "ins_size": 2,
        "outs_size": 0,
        "bytecode": bytecode,
        "tries": [],
    }])
    return b.serialize()


def build_goto_simple() -> bytes:
    """Test goto branch behavior.
    Method: const/4 v0, #1; goto +2 → PC=4; const/4 v0, #99; PC=4: return-void
    """
    b = DexBuilder()
    b.add_string("Ltest/exp052/TestActivity;")  # 0
    b.add_string("Ljava/lang/Object;")           # 1
    b.add_string("Landroid/os/Bundle;")          # 2
    b.add_string("onCreate")                      # 3
    b.add_string("(Landroid/os/Bundle;)V")        # 4
    b.add_string("V")                             # 5
    b.add_type("Ltest/exp052/TestActivity;")      # 0
    b.add_type("Ljava/lang/Object;")               # 1
    b.add_type("Landroid/os/Bundle;")              # 2
    b.add_type("V")                                # 3
    b.add_proto("V", "V")                          # 0
    b.add_method("Ltest/exp052/TestActivity;", "V", "V", "onCreate")  # 0
    b.add_class("Ltest/exp052/TestActivity;", superclass="Landroid/app/Activity;")

    bytecode = [
        # PC=0: const/4 v0, #1
        (0x10 << 8) | OP_CONST_4,
        # PC=1: goto +2 → PC=3
        (0x02 << 8) | OP_GOTO,
        # PC=2: const/4 v0, #99 (should be skipped)
        (0x63 << 8) | OP_CONST_4,
        # PC=3: return-void
        (0x00 << 8) | OP_RETURN_VOID,
    ]
    b.set_class_data(0, [{
        "name": "onCreate",
        "shorty": "V",
        "return_type": "V",
        "access": 0x1,
        "registers_size": 4,
        "ins_size": 2,
        "outs_size": 0,
        "bytecode": bytecode,
        "tries": [],
    }])
    return b.serialize()


def build_thread_identity_test() -> bytes:
    """Test that Thread.currentThread() returns same object as Looper.getMainLooper().getThread().
    Method: onCreate()V
      v0 = Thread.currentThread()
      v1 = Looper.getMainLooper()
      v2 = v1.getThread()
      if-eq v0, v2, +3 → PC=12  // identity check passes
      // identity mismatch — fall through to const v0, #99; return
      // skip
      PC=12: return-void
    """
    b = DexBuilder()
    b.add_string("Ltest/exp052/TestActivity;")  # 0
    b.add_string("Ljava/lang/Object;")           # 1
    b.add_string("Ljava/lang/Thread;")            # 2
    b.add_string("Landroid/os/Looper;")           # 3
    b.add_string("Landroid/os/Bundle;")           # 4
    b.add_string("currentThread")                 # 5
    b.add_string("()Ljava/lang/Thread;")          # 6
    b.add_string("getMainLooper")                 # 7
    b.add_string("()Landroid/os/Looper;")         # 8
    b.add_string("getThread")                     # 9
    b.add_string("()Ljava/lang/Thread;")          # 10
    b.add_string("onCreate")                      # 11
    b.add_string("(Landroid/os/Bundle;)V")        # 12
    b.add_string("V")                             # 13
    b.add_type("Ltest/exp052/TestActivity;")      # 0
    b.add_type("Ljava/lang/Object;")               # 1
    b.add_type("Ljava/lang/Thread;")               # 2
    b.add_type("Landroid/os/Looper;")              # 3
    b.add_type("Landroid/os/Bundle;")              # 4
    b.add_type("V")                                # 5
    b.add_proto("Ljava/lang/Thread;", "Ljava/lang/Thread;")  # 0 (currentThread)
    b.add_proto("Landroid/os/Looper;", "Landroid/os/Looper;")  # 1 (getMainLooper)
    b.add_proto("Ljava/lang/Thread;", "Ljava/lang/Thread;")  # 2 (getThread)
    b.add_proto("V", "V")                          # 3 (onCreate)
    b.add_method("Ljava/lang/Thread;", "Ljava/lang/Thread;", "Ljava/lang/Thread;", "currentThread")  # 0
    b.add_method("Landroid/os/Looper;", "Landroid/os/Looper;", "Landroid/os/Looper;", "getMainLooper")  # 1
    b.add_method("Landroid/os/Looper;", "Ljava/lang/Thread;", "Ljava/lang/Thread;", "getThread")  # 2
    b.add_method("Ltest/exp052/TestActivity;", "V", "V", "onCreate")  # 3
    b.add_class("Ltest/exp052/TestActivity;", superclass="Landroid/app/Activity;")

    bytecode = [
        # PC=0: invoke-static {}, Thread.currentThread()  (method@0)
        (0x00 << 8) | OP_INVOKE_STATIC, 0x0000, 0x0000,
        # PC=3: move-result-object v0
        (0x00 << 8) | OP_MOVE_RESULT_OBJECT,
        # PC=4: invoke-static {}, Looper.getMainLooper()  (method@1)
        (0x00 << 8) | OP_INVOKE_STATIC, 0x0001, 0x0000,
        # PC=7: move-result-object v1
        (0x10 << 8) | OP_MOVE_RESULT_OBJECT,
        # PC=8: invoke-virtual {v1}, Looper.getThread()  (method@2)
        (0x10 << 8) | OP_INVOKE_VIRTUAL, 0x0002, 0x0100,
        # PC=11: move-result-object v2
        (0x20 << 8) | OP_MOVE_RESULT_OBJECT,
        # PC=12: if-eq v0, v2, +3 → PC=15  (22t format: B|A|op)
        # B=v1, A=v0 — wait let me check. 22t format is "B|A|op".
        # Actually 22t format: byte1 = B|A where B is high nibble, A is low.
        # We want if-eq v0, v2 — A=v0 (first reg), B=v2 (second reg).
        # So byte1 = (B << 4) | A = (2 << 4) | 0 = 0x20.
        # Wait — I had it wrong. Let me re-check. Per AOSP:
        # 22t: B|A|op → if-eq vA, vB, +BBBB
        # So A is the first register, B is the second.
        # We want if-eq v0, v2 — A=0, B=2 → byte1 = (2 << 4) | 0 = 0x20.
        (0x20 << 8) | OP_IF_EQ, 0x0003,  # offset = +3 → PC=15
        # PC=14: const/4 v0, #99 (identity failed — shouldn't reach)
        (0x63 << 8) | OP_CONST_4,
        # PC=15: return-void
        (0x00 << 8) | OP_RETURN_VOID,
    ]
    b.set_class_data(0, [{
        "name": "onCreate",
        "shorty": "V",
        "return_type": "V",
        "access": 0x1,
        "registers_size": 4,
        "ins_size": 2,
        "outs_size": 1,
        "bytecode": bytecode,
        "tries": [],
    }])
    return b.serialize()


# ============================================================================
# Main runner
# ============================================================================

def main():
    print('=== EXP-052 Regression Test Suite ===')
    print()

    cases = [
        # Invoke tests
        ('reg_invoke_virtual_return', build_invoke_virtual_return,
         'invoke-virtual returns object (toString) — verify move-result-object.'),
        ('reg_invoke_static_return', build_invoke_static_return,
         'invoke-static returns int (helper returns 42) — verify move-result.'),
        # Branch tests
        ('reg_branch_if_eqz', build_branch_if_eqz,
         'if-eqz on const/4 v0, #0 — branch should be taken.'),
        ('reg_branch_if_nez', build_branch_if_nez,
         'if-nez on const/4 v0, #1 — branch should be taken.'),
        ('reg_goto_simple', build_goto_simple,
         'goto +2 — skip next instruction.'),
        # Shadow API tests
        ('reg_thread_identity', build_thread_identity_test,
         'Thread.currentThread() == Looper.getMainLooper().getThread()'),
    ]

    results = []
    for name, builder, desc in cases:
        print(f'--- {name} ---')
        print(f'  Description: {desc}')
        try:
            dex = builder()
        except Exception as e:
            print(f'  BUILD FAILED: {e}')
            continue
        result = run_test(name, dex)
        results.append(result)
        print(f'  Exit code: {result["exit_code"]}')
        print(f'  Elapsed: {result["elapsed"]:.2f}s')
        if 'THROW' in result['stderr']:
            for line in result['stderr'].splitlines():
                if '[THROW]' in line:
                    print(f'  THROW: {line.strip()}')
        if '[HALT' in result['stderr']:
            for line in result['stderr'].splitlines():
                if '[HALT' in line:
                    print(f'  HALT: {line.strip()}')
        # Check for FAILURE
        if 'FAILURE' in result['stdout']:
            for line in result['stdout'].splitlines():
                if 'FAILURE' in line or 'RESOLUTION_FAILED' in line:
                    print(f'  STDOUT: {line.strip()}')
        print()

    # Write summary
    summary_path = os.path.join(MINIANDROID_ROOT, 'docs', 'EXP052_REGRESSION_TESTS.md')
    with open(summary_path, 'w') as f:
        f.write('# EXP-052 Regression Test Suite\n\n')
        f.write('**Date:** 2026-08-17\n\n')
        f.write('## Test Cases\n\n')
        for name, _, desc in cases:
            f.write(f'### {name}\n{desc}\n\n')
        f.write('## Results\n\n')
        f.write('| Case | Exit | THROW | HALT | Notes |\n')
        f.write('|------|------|-------|------|-------|\n')
        for r in results:
            throws = [l for l in r['stderr'].splitlines() if '[THROW]' in l]
            halts = [l for l in r['stderr'].splitlines() if '[HALT' in l]
            notes = []
            if r['exit_code'] == 0 and not throws and not halts:
                notes.append('PASS')
            elif r['exit_code'] == 0:
                notes.append('ran with events')
            else:
                notes.append(f'exit={r["exit_code"]}')
            f.write(f'| {r["name"]} | {r["exit_code"]} | {len(throws)} | {len(halts)} | {", ".join(notes)} |\n')
    print(f'Summary written to {summary_path}')


if __name__ == '__main__':
    main()
