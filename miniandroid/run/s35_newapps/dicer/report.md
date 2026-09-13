# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/my-project/apk_cache/s35new/org.secuso.privacyfriendlydicer_101.apk`
- **Package:** `org.secuso.privacyfriendlydicer`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 1 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 1 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 2188 |
| `TraceEngine` | 2 |
| `Unknown` | 1 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 2160 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_capture_output` | 2 |
| `ExecutionEngine.stage_render_frame` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `Unknown.Unknown` | 1 |
| `TraceEngine.start_session` | 1 |
| `TraceEngine.log_screenshot` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |
| `ExecutionEngine.execution_source` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalStateException; escaped the app boundary at Lorg/secuso/pfacore/ui/activities/SplashActivity;.onCreate invoke_pc=0x5 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `run/s35_newapps/dicer/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](run/s35_newapps/dicer/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260913-173207-1193`
- **Generated:** 2026-09-13 17:32:08 UTC
