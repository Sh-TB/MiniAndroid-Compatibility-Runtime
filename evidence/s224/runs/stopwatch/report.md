# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s224/runs/store_stopwatch/data/app/com.github.muellerma.stopwatch/base.apk`
- **Package:** `com.github.muellerma.stopwatch`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 13 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 0 |
| Warnings | 14 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 1119 |
| `TraceEngine` | 3 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 1061 |
| `ExecutionEngine.stage_render_frame` | 26 |
| `ExecutionEngine.stage_capture_output` | 7 |
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
| `ExecutionEngine.execution_source` | 1 |

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s224/runs/stopwatch/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](/home/z/my-project/evidence/s224/runs/stopwatch/screenshot.png)
- **SHA256:** `31ddd4d5b8e6d18e4a14cd38a44bd355b4e809de97f3f97bcd669ac103838093` (recorded by tools/report_sanity_fix.py from the actual retained file)

## Session Info

- **Session ID:** `EXP-001-20261112-081853-3025`
- Run id: `EXP-001-20261112-081853-3025` (derived from the report\'s own Session ID line)
- **Generated:** 2026-11-12 08:18:55 UTC
