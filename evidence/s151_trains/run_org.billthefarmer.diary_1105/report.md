# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s151_trains/store_org.billthefarmer.diary_1105/data/data/app/org.billthefarmer.diary/base.apk`
- **Package:** `org.billthefarmer.diary`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 4 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 390 |
| `TraceEngine` | 3 |
| `Unknown` | 4 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 348 |
| `ExecutionEngine.stage_capture_output` | 8 |
| `ExecutionEngine.stage_render_frame` | 7 |
| `ExecutionEngine.trace_files` | 5 |
| `Unknown.Unknown` | 4 |
| `ExecutionEngine.phase_b_click` | 4 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |
| `ExecutionEngine.execution_source` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.create_view_from_dalvik_result` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lorg/billthefarmer/diary/Diary;.setDate invoke_pc=0x4 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lorg/billthefarmer/diary/Diary;.changeDate invoke_pc=0xa depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lorg/billthefarmer/diary/Diary;.today invoke_pc=0x1d depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lorg/billthefarmer/diary/Diary;.onCreate invoke_pc=0xe4 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s151_trains/run_org.billthefarmer.diary_1105/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s151_trains/run_org.billthefarmer.diary_1105/screenshot.png)
- **SHA256:** `b18c3ee6c28185609c5edc24be8b8ec5e7527c5ae3696b4c11e3087742e74c26` (recorded by tools/report_sanity_fix.py from the actual retained file)

## Session Info

- **Session ID:** `EXP-001-20261102-161714-0416`
- **Generated:** 2026-11-02 16:17:15 UTC
