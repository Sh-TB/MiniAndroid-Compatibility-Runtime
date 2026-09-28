# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/tmp/s115_apks/ru.hyst329.openfool_30.apk`
- **Package:** `ru.hyst329.openfool`
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
| `ExecutionEngine` | 3245 |
| `TraceEngine` | 3 |
| `Unknown` | 7 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 3210 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/RuntimeException; unwound Landroid/support/multidex/MultiDexApplication;.attachBaseContext invoke_pc=0x3 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/RuntimeException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/GdxRuntimeException; unwound Lcom/badlogic/gdx/backends/android/AndroidGraphics;.<init> invoke_pc=0x5a depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/GdxRuntimeException; unwound Lcom/badlogic/gdx/backends/android/AndroidGraphics;.<init> invoke_pc=0x1 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/GdxRuntimeException; unwound Lcom/badlogic/gdx/backends/android/AndroidApplication;.init invoke_pc=0x1e depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/GdxRuntimeException; unwound Lcom/badlogic/gdx/backends/android/AndroidApplication;.initialize invoke_pc=0x1 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Lcom/badlogic/gdx/utils/GdxRuntimeException; escaped the app boundary at Lru/hyst329/openfool/AndroidLauncher;.onCreate invoke_pc=0x1e depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s115_sweep/t83_ru.hyst329.openfool/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s115_sweep/t83_ru.hyst329.openfool/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s115_sweep/t83_ru.hyst329.openfool/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s115_sweep/t83_ru.hyst329.openfool/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260928-052643-4605`
- **Generated:** 2026-09-28 05:26:43 UTC
