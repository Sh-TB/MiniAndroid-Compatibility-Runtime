# EXP-052 Exception Handling Validation Suite

**Date:** 2026-08-17

## Test Cases

### case1_no_catch
Throw with no try table — method should halt cleanly, caller continues.

### case2_local_catch
Throw inside try{}; catch-all handler exists — handler should run.

### case3_nested_catch
B() throws; A() has catch — stack should unwind from B to A.

### case4_catch_all
Catch-all handler — same as case2.

## Results

| Case | Exit | THROW events | HALT events | Has try table (in test) |
|------|------|--------------|-------------|--------------------------|
| case1_no_catch | 0 | 0 | 0 | — |
| case2_local_catch | 0 | 0 | 0 | — |
| case3_nested_catch | 0 | 0 | 0 | — |
| case4_catch_all | 0 | 0 | 0 | — |

## Per-case Details

### case1_no_catch

- Exit code: 0
- Elapsed: 0.02s

### case2_local_catch

- Exit code: 0
- Elapsed: 0.02s

### case3_nested_catch

- Exit code: 0
- Elapsed: 0.02s

### case4_catch_all

- Exit code: 0
- Elapsed: 0.02s

