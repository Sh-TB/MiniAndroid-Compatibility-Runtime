# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s188_w16/runs/store_org.nitri.opentopo/data/app/org.nitri.opentopo/base.apk`
- **Package:** `org.nitri.opentopo`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 15 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 4 |
| Warnings | 1 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 4781 |
| `TraceEngine` | 3 |
| `Unknown` | 4 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 4718 |
| `ExecutionEngine.stage_render_frame` | 30 |
| `ExecutionEngine.stage_capture_output` | 7 |
| `ExecutionEngine.trace_files` | 5 |
| `Unknown.Unknown` | 4 |
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

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/io/IOException; unwound Ljl2;.<init> invoke_pc=0xd depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/RuntimeException; unwound Lnet/danlew/android/joda/JodaTimeInitializer;.b invoke_pc=0x39 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Luw; unwound Lig;.n invoke_pc=0x55 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Luw; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s188_w16/runs/org.nitri.opentopo/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s188_w16/runs/org.nitri.opentopo/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s188_w16/runs/org.nitri.opentopo/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s188_w16/runs/org.nitri.opentopo/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261108-050327-1876`
- **Generated:** 2026-11-08 05:03:31 UTC
