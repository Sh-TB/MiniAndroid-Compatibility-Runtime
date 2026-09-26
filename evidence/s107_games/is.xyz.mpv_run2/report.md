# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/s107_apks/is.xyz.mpv.apk`
- **Package:** `is.xyz.mpv`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 7 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 1330 |
| `TraceEngine` | 3 |
| `Unknown` | 7 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 1294 |
| `Unknown.Unknown` | 7 |
| `ExecutionEngine.stage_capture_output` | 6 |
| `ExecutionEngine.trace_files` | 5 |
| `ExecutionEngine.stage_render_frame` | 4 |
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
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |
| `ExecutionEngine.execution_source` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/activity/ComponentActivity;.onCreate invoke_pc=0x2e depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lis/xyz/mpv/MainActivity;.onCreate invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/appcompat/app/AppCompatDelegateImpl;.ensureSubDecor invoke_pc=0x2a3 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/appcompat/app/AppCompatDelegateImpl;.initWindowDecorActionBar invoke_pc=0x0 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/appcompat/app/AppCompatActivity;.getSupportActionBar invoke_pc=0x6 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalStateException; escaped the app boundary at Lis/xyz/mpv/MainActivity;.onCreate invoke_pc=0x3 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalStateException; escaped the app boundary at Lis/xyz/mpv/MainActivity;.onCreate invoke_pc=0x4a depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/is.xyz.mpv_run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/is.xyz.mpv_run2/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/is.xyz.mpv_run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/is.xyz.mpv_run2/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260926-175257-1310`
- **Generated:** 2026-09-26 17:52:57 UTC
