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
| Errors | 9 |
| Warnings | 32 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 4241 |
| `TraceEngine` | 3 |
| `Unknown` | 9 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 4146 |
| `ExecutionEngine.stage_render_frame` | 62 |
| `Unknown.Unknown` | 9 |
| `ExecutionEngine.stage_capture_output` | 7 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_initialize_runtime` | 3 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
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

- **Message:** [EXC-UNWIND] Ln4/c; unwound Lu4/a;.a invoke_pc=0x91 depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ln4/c; unwound LB1/A;.j invoke_pc=0x1b depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ln4/c; unwound LE/e0;.a invoke_pc=0x4 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ln4/c; unwound LB1/A;.h invoke_pc=0x0 depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ln4/c; unwound LA/b0;.z invoke_pc=0x53 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ln4/c; unwound La3/c;.E invoke_pc=0x64 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ln4/c; unwound Lb/k;.b invoke_pc=0x38 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ln4/c; unwound LY2/n;.getValue invoke_pc=0xb depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ln4/c; escaped the app boundary at Lcom/farmerbb/notepad/android/NotepadActivity;.onCreate invoke_pc=0xc depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `evidence/s26/w1_np/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](evidence/s26/w1_np/screenshot.png)

### Output Frame

- **File:** `evidence/s26/w1_np/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](evidence/s26/w1_np/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261122-171545-0629`
- **Generated:** 2026-11-22 17:15:51 UTC
