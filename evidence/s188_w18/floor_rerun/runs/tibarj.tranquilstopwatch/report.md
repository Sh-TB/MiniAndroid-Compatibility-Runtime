# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s188_w18/floor_rerun/runs/store_tibarj.tranquilstopwatch/data/app/tibarj.tranquilstopwatch/base.apk`
- **Package:** `tibarj.tranquilstopwatch`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 15 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 6 |
| Warnings | 1 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 1518 |
| `TraceEngine` | 3 |
| `Unknown` | 6 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 1455 |
| `ExecutionEngine.stage_render_frame` | 30 |
| `ExecutionEngine.stage_capture_output` | 7 |
| `Unknown.Unknown` | 6 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `TraceEngine.start_session` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.stage_frame_sequence` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lb1/a0;.<init> invoke_pc=0x47 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Ltibarj/tranquilstopwatch/ClockFragment;.<init> invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Ltibarj/tranquilstopwatch/MainActivity;.onCreate invoke_pc=0x23 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lb1/a0;.<init> invoke_pc=0x47 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Ltibarj/tranquilstopwatch/StopwatchFragment;.<init> invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Ltibarj/tranquilstopwatch/MainActivity;.onCreate invoke_pc=0x23 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s188_w18/floor_rerun/runs/tibarj.tranquilstopwatch/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s188_w18/floor_rerun/runs/tibarj.tranquilstopwatch/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s188_w18/floor_rerun/runs/tibarj.tranquilstopwatch/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s188_w18/floor_rerun/runs/tibarj.tranquilstopwatch/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261108-212835-6332`
- **Generated:** 2026-11-08 21:28:38 UTC
