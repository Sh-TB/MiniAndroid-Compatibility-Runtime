# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s200/runs/store_mtm_persist_final/data/app/dubrowgn.microtimer/base.apk`
- **Package:** `dubrowgn.microtimer`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 11 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 0 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 221 |
| `TraceEngine` | 3 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 144 |
| `ExecutionEngine.stage_render_frame` | 44 |
| `ExecutionEngine.stage_capture_output` | 8 |
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

- **File:** `/home/z/my-project/evidence/s200/runs/mtm_persist_final_B/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s200/runs/mtm_persist_final_B/screenshot.png)
- **SHA256:** `47ad887bf05c9c1d3287b8b84303b5f3c0d7ed6b8b7dccddec1811a450782675` (recorded by tools/report_sanity_fix.py from the actual retained file)

## Session Info

- **Session ID:** `EXP-001-20261108-212942-1565`
- Run id: `EXP-001-20261108-212942-1565` (derived from the report\'s own Session ID line)
- **Generated:** 2026-11-08 21:29:44 UTC
