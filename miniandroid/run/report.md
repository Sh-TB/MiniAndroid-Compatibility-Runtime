# MiniAndroid Execution Report

## Application

- **APK:** `test_apks/HelloWorld.apk`
- **Package:** `com.miniandroid.hello`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 1 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 0 |
| Warnings | 1 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 19 |
| `TraceEngine` | 2 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_capture_output` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_load_classes` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_render_frame` | 2 |
| `ExecutionEngine.create_hello_world_view` | 1 |
| `ExecutionEngine.lifecycle_fallback` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `ExecutionEngine.validation` | 1 |
| `TraceEngine.log_screenshot` | 1 |
| `TraceEngine.start_session` | 1 |

## Screenshots

### Output Frame

- **File:** `./run/screenshot.ppm`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](./run/screenshot.ppm)

## Session Info

- **Session ID:** `EXP-001-20260813-212321-4633`
- **Generated:** 2026-08-13 21:23:21 UTC
