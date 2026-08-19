#!/usr/bin/env python3
"""
EXP-053 Task 1: Exception catch-all handler validation.

Tests that the runtime correctly jumps to the catch-all handler when
a throw occurs inside a try{} block.

Test cases:
  Case A: try { throw } catch(...) { continue } — handler should run
  Case B: throw (no try) — method should abort

Expected:
  Case A: handler is reached, method returns successfully (exit 0)
  Case B: THROW event logged, method halts
"""
import os, sys, struct, subprocess, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp052_exception_tests import (
    DexBuilder, run_test, wrap_in_apk, MINIANDROID_ROOT, RUNTIME_BIN,
    OP_CONST_4, OP_NEW_INSTANCE, OP_INVOKE_DIRECT, OP_THROW,
    OP_RETURN_VOID, OP_RETURN, OP_MOVE_EXCEPTION, OP_GOTO,
)

def build_case_a_catch_all() -> bytes:
    """Case A: try { throw } catch(...) { return 42 }
    Method: onCreate()V — but we'll make it return int 42.
    Actually onCreate returns void. So we'll do:
      try { throw new RuntimeException }
      catch(...) { return-void }  <- catch-all
    PC=0: new-instance v0, RuntimeException
    PC=2: invoke-direct {v0}, RuntimeException.<init>()V
    PC=5: throw v0          <- exception source
    PC=6: move-exception v0  <- catch handler start
    PC=7: return-void
    """
    b = DexBuilder()
    b.add_string("Ltest/exp052/TestActivity;")  # 0
    b.add_string("Ljava/lang/Object;")           # 1
    b.add_string("Ljava/lang/RuntimeException;") # 2
    b.add_string("Landroid/os/Bundle;")          # 3
    b.add_string("<init>")                        # 4
    b.add_string("()V")                           # 5
    b.add_string("onCreate")                      # 6
    b.add_string("(Landroid/os/Bundle;)V")        # 7
    b.add_string("V")                             # 8
    b.add_type("Ltest/exp052/TestActivity;")      # 0
    b.add_type("Ljava/lang/Object;")               # 1
    b.add_type("Ljava/lang/RuntimeException;")    # 2
    b.add_type("Landroid/os/Bundle;")              # 3
    b.add_type("V")                                # 4
    b.add_proto("V", "V")                          # 0 (init)
    b.add_proto("V", "V")                          # 1 (onCreate)
    b.add_method("Ljava/lang/RuntimeException;", "V", "V", "<init>")  # 0
    b.add_method("Ltest/exp052/TestActivity;", "V", "V", "onCreate")   # 1
    b.add_class("Ltest/exp052/TestActivity;", superclass="Landroid/app/Activity;")
    bytecode = [
        # PC=0: new-instance v2, RuntimeException  (type_idx=2)
        (OP_NEW_INSTANCE << 8) | 0x02, 0x0002,
        # PC=2: invoke-direct {v2}, RuntimeException.<init>()V  (method@0)
        (0x10 << 8) | OP_INVOKE_DIRECT, 0x0000, 0x0200,
        # PC=5: throw v2  <- exception source
        (0x02 << 8) | OP_THROW,
        # PC=6: move-exception v2  <- catch handler start (catch-all)
        (0x02 << 8) | OP_MOVE_EXCEPTION,
        # PC=7: return-void
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
        "tries": [{
            "start_addr": 0,
            "insn_count": 6,  # PC 0..5 covered (the throw at PC=5 is the last)
            "handler_off": 1,
            "handlers": [(None, 6)],  # catch-all at PC=6
        }],
    }])
    return b.serialize()


def build_case_b_no_catch() -> bytes:
    """Case B: throw without try — method should abort.
    Same as case1_no_catch from exp052 tests.
    """
    from exp052_exception_tests import build_case1_no_catch
    return build_case1_no_catch()


def main():
    print('=== EXP-053 Task 1: Exception catch-all handler ===')
    print()

    cases = [
        ('case_a_catch_all', build_case_a_catch_all,
         'try { throw } catch(...) { return } — handler should run, method completes'),
        ('case_b_no_catch', build_case_b_no_catch,
         'throw without try — method should halt with THROW event'),
    ]

    results = []
    for name, builder, desc in cases:
        print(f'--- {name} ---')
        print(f'  Description: {desc}')
        dex = builder()
        result = run_test(name, dex)
        results.append(result)
        print(f'  Exit code: {result["exit_code"]}')
        # Look for THROW, EXCEPTION, HALT, METHOD-IN
        for line in result['stderr'].splitlines():
            for marker in ['[THROW]', '[EXCEPTION]', '[HALT', '[METHOD-IN]']:
                if marker in line:
                    print(f'  {line.strip()}')
                    break
        # Look for handler reached signal
        if 'handler_addr' in result['stderr']:
            for line in result['stderr'].splitlines():
                if 'handler_addr' in line:
                    print(f'  HANDLER: {line.strip()}')
        print()

    # Check expected results
    print('=== Expected vs Actual ===')
    for r, expected in zip(results, ['handler reached', 'THROW halt']):
        throws = [l for l in r['stderr'].splitlines() if '[THROW]' in l]
        exceptions = [l for l in r['stderr'].splitlines() if '[EXCEPTION]' in l]
        print(f'  {r["name"]}: expected={expected}, throws={len(throws)}, exceptions={len(exceptions)}')

    # Write summary
    summary_path = os.path.join(MINIANDROID_ROOT, 'docs', 'EXP053_TASK1_EXCEPTION_TESTS.md')
    with open(summary_path, 'w') as f:
        f.write('# EXP-053 Task 1 — Exception catch-all handler tests\n\n')
        f.write('**Date:** 2026-08-17\n\n')
        f.write('## Test Cases\n\n')
        for name, _, desc in cases:
            f.write(f'### {name}\n{desc}\n\n')
        f.write('## Results\n\n')
        for r in results:
            f.write(f'### {r["name"]}\n')
            f.write(f'- Exit code: {r["exit_code"]}\n')
            throws = [l for l in r['stderr'].splitlines() if '[THROW]' in l]
            exceptions = [l for l in r['stderr'].splitlines() if '[EXCEPTION]' in l]
            f.write(f'- THROW events: {len(throws)}\n')
            f.write(f'- EXCEPTION events: {len(exceptions)}\n')
            for l in throws[:3]:
                f.write(f'  - `{l.strip()}`\n')
            for l in exceptions[:3]:
                f.write(f'  - `{l.strip()}`\n')
            f.write('\n')
    print(f'Summary at {summary_path}')


if __name__ == '__main__':
    main()
