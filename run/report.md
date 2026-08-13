# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/miniandroid/test_apks/HelloWorld.apk`
- **Package:** `com.miniandroid.hello`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 0 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 1 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 12 |
| `TraceEngine` | 1 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_load_classes` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `TraceEngine.start_session` | 1 |

## Errors & Issues

### REAL_EXECUTION_ASSERTION_FAIL

- **Message:** EXP-031.5 ASSERTION FAILED: REAL_DALVIK mode selected but ExecuteInstruction() was never called. This means no actual Dalvik bytecode was executed. Possible causes: (1) DEX parser did not extract method bytecode, (2) No methods found matching entry point criteria, (3) All methods had empty bytecode arrays. Instructions expected: > 0, Actual: 0
- **Location:** `ExecutionEngine.stage_execute_application_real_dalvik`
- **Fatal:** No

## Session Info

- **Session ID:** `EXP-001-20260813-215307-3356`
- **Generated:** 2026-08-13 21:53:07 UTC
