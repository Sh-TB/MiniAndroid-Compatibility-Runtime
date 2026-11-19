# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/miniandroid/evidence/w21/apk_src/com.uberspot.a2048_25.apk`
- **Package:** `com.uberspot.a2048`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 14 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 6 |
| Warnings | 1 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 148 |
| `TraceEngine` | 3 |
| `Unknown` | 6 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 87 |
| `ExecutionEngine.stage_render_frame` | 28 |
| `ExecutionEngine.stage_capture_output` | 7 |
| `Unknown.Unknown` | 6 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lde/cketti/changelog/MergedChangeLogProvider;.getChangeLog invoke_pc=0x2 depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lde/cketti/changelog/ChangeLog;.getChangeLog invoke_pc=0x2 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lde/cketti/changelog/dialog/DialogChangeLog;.getChangeLogHtml invoke_pc=0x4 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lde/cketti/changelog/dialog/DialogChangeLog;.getDialog invoke_pc=0x7 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lde/cketti/changelog/dialog/DialogChangeLog;.getLogDialog invoke_pc=0x6 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lcom/uberspot/a2048/MainActivity;.onCreate invoke_pc=0x54 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `evidence/w21/a2048_probe/pristine/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](evidence/w21/a2048_probe/pristine/screenshot.png)

### Output Frame

- **File:** `evidence/w21/a2048_probe/pristine/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](evidence/w21/a2048_probe/pristine/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261119-132736-9755`
- **Generated:** 2026-11-19 13:27:39 UTC
