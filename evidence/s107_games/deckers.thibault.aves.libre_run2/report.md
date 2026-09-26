# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/s107_apks/deckers.thibault.aves.libre.apk`
- **Package:** `deckers.thibault.aves.libre`
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
| `ExecutionEngine` | 3999 |
| `TraceEngine` | 3 |
| `Unknown` | 5 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 3962 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Ls01;.g invoke_pc=0x7 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Ldeckers/thibault/aves/MainActivity;.<clinit> invoke_pc=0xc depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Ldeckers/thibault/aves/MainActivity;.onCreate invoke_pc=0x12 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ly40;.onCreate invoke_pc=0x42f depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalStateException; escaped the app boundary at Ldeckers/thibault/aves/MainActivity;.onCreate invoke_pc=0x20 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/deckers.thibault.aves.libre_run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/deckers.thibault.aves.libre_run2/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/deckers.thibault.aves.libre_run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/deckers.thibault.aves.libre_run2/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260926-173452-4661`
- **Generated:** 2026-09-26 17:34:53 UTC
