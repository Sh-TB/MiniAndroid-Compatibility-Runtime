# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/s107_apks/com.chmouel.liseur.apk`
- **Package:** `com.chmouel.liseur`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 5 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 8129 |
| `TraceEngine` | 3 |
| `Unknown` | 5 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 8092 |
| `ExecutionEngine.stage_capture_output` | 6 |
| `Unknown.Unknown` | 5 |
| `ExecutionEngine.trace_files` | 5 |
| `ExecutionEngine.stage_render_frame` | 4 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |
| `ExecutionEngine.execution_source` | 1 |
| `ExecutionEngine.drain_handler_queue` | 1 |
| `ExecutionEngine.deferred_runnables` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Lmh0;.<init> invoke_pc=0x17 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Lui;.<init> invoke_pc=0x41 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Lcom/chmouel/liseur/LiseurApplication;.onCreate invoke_pc=0x5 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/UnsupportedOperationException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lcom/chmouel/liseur/MainActivity;.onCreate invoke_pc=0x19 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/com.chmouel.liseur_run1/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/com.chmouel.liseur_run1/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/com.chmouel.liseur_run1/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/com.chmouel.liseur_run1/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260926-180112-0731`
- **Generated:** 2026-09-26 18:01:13 UTC
