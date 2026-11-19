# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/upload/handoff_apks/com.farmerbb.notepad_122.apk`
- **Package:** `com.farmerbb.notepad`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 31 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 5 |
| Warnings | 32 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 4242 |
| `TraceEngine` | 3 |
| `Unknown` | 5 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 4146 |
| `ExecutionEngine.stage_render_frame` | 62 |
| `ExecutionEngine.stage_capture_output` | 7 |
| `Unknown.Unknown` | 5 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_initialize_runtime` | 3 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lz1/h;.a invoke_pc=0x0 depth=28
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lv1/F;.h invoke_pc=0x6e depth=26
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lv1/F;.d invoke_pc=0xa7 depth=25
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lu2/h;.t invoke_pc=0xe depth=22
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lw2/t;.t invoke_pc=0x41 depth=7
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `evidence/w20/runtime_perf/com.farmerbb.notepad_122_r5/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](evidence/w20/runtime_perf/com.farmerbb.notepad_122_r5/screenshot.png)

### Output Frame

- **File:** `evidence/w20/runtime_perf/com.farmerbb.notepad_122_r5/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](evidence/w20/runtime_perf/com.farmerbb.notepad_122_r5/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261119-114046-9977`
- **Generated:** 2026-11-19 11:40:53 UTC
