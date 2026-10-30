# MiniAndroid Execution Report

## Application

- **APK:** `upload/canonical_apks/dooz_23_toplevel.apk`
- **Package:** `io.github.yamin8000.dooz`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 13 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 20 |
| Warnings | 1 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 3113 |
| `TraceEngine` | 3 |
| `Unknown` | 20 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 3053 |
| `ExecutionEngine.stage_render_frame` | 26 |
| `Unknown.Unknown` | 20 |
| `ExecutionEngine.stage_capture_output` | 7 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
| `ExecutionEngine.stage_frame_sequence` | 1 |
| `TraceEngine.start_session` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Ljj;.b invoke_pc=0x3e depth=10
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lpm;.B invoke_pc=0xf depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Le2;.a invoke_pc=0x43 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lio/github/yamin8000/dooz/ui/MainActivity;.d invoke_pc=0x4 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lae0;.a invoke_pc=0x9 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Ljm;.onCreate invoke_pc=0x1e depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lio/github/yamin8000/dooz/ui/MainActivity;.l invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lio/github/yamin8000/dooz/ui/MainActivity;.onCreate invoke_pc=0xb4 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lqi0;.S invoke_pc=0x1e depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Le;.q invoke_pc=0x1d8 depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lio/github/yamin8000/dooz/ui/MainActivity;.onCreate invoke_pc=0xc1 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lu52;.<clinit> invoke_pc=0xb depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lv52;.<clinit> invoke_pc=0x0 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lfh0;.<init> invoke_pc=0xb depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lt4;.<init> invoke_pc=0x75 depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound La72;.a invoke_pc=0x67 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lr;.onMeasure invoke_pc=0x0 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Ljm;.setContentView invoke_pc=0x13 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lio/github/yamin8000/dooz/ui/MainActivity;.onCreate invoke_pc=0x132 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `tmp/s134_train3_run6/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](tmp/s134_train3_run6/screenshot.png)

### Output Frame

- **File:** `tmp/s134_train3_run6/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](tmp/s134_train3_run6/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261030-070400-6321`
- **Generated:** 2026-10-30 07:04:03 UTC
