# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s215/runs/store_ar_probe/data/app/com.probe.ar/base.apk`
- **Package:** `com.probe.ar`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 9 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 0 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 53 |
| `TraceEngine` | 3 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_render_frame` | 18 |
| `ExecutionEngine.stage_capture_output` | 6 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_load_classes` | 3 |
| `ExecutionEngine.create_view_from_dalvik_result` | 2 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
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

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s215/runs/ar_probe/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 272.05 KB

![Screenshot](/home/z/my-project/evidence/s215/runs/ar_probe/screenshot.png)
- **SHA256:** `a48cf00b1670110911d5c5fc29c7f1bc881f001b2f8e8aff99d23e8ea00cbdc2` (recorded by tools/report_sanity_fix.py from the actual retained file)

## Session Info

- **Session ID:** `EXP-001-20261111-055243-2322`
- Run id: `EXP-001-20261111-055243-2322` (derived from the report\'s own Session ID line)
- **Generated:** 2026-11-11 05:52:44 UTC
