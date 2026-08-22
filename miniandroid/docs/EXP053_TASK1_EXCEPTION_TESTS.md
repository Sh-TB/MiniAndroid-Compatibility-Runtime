# EXP-053 Task 1 — Exception catch-all handler tests

**Date:** 2026-08-17

## Test Cases

### case_a_catch_all
try { throw } catch(...) { return } — handler should run, method completes

### case_b_no_catch
throw without try — method should halt with THROW event

## Results

### case_a_catch_all
- Exit code: 0
- THROW events: 0
- EXCEPTION events: 2
  - `[EXCEPTION] method=Ltest/exp052/TestActivity;.onCreate pc=5 exception=<unknown> try_range=[0,6) handler=FOUND handler_addr=6 catch_type=<catch-all>`
  - `[EXCEPTION] → jumping to catch-all handler at PC=6`

### case_b_no_catch
- Exit code: 0
- THROW events: 0
- EXCEPTION events: 1
  - `[EXCEPTION] method=Ltest/exp052/TestActivity;.onCreate pc=5 exception=<unknown> try_range=(none) handler=NOT_FOUND`

