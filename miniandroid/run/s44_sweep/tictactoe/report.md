# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/my-project/apk_cache/corpus/tictactoeemmanuelmess.apk`
- **Package:** `com.emmanuelmess.tictactoe`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 1 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 5 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 2168 |
| `TraceEngine` | 2 |
| `Unknown` | 5 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 2138 |
| `Unknown.Unknown` | 5 |
| `ExecutionEngine.trace_files` | 5 |
| `ExecutionEngine.stage_capture_output` | 3 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_render_frame` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `TraceEngine.start_session` | 1 |
| `TraceEngine.log_screenshot` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |
| `ExecutionEngine.execution_source` | 1 |

## Errors & Issues

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

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/GdxRuntimeException; unwound Lcom/badlogic/gdx/backends/android/AndroidApplication;.initializeForView invoke_pc=0x1 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Lcom/badlogic/gdx/utils/GdxRuntimeException; escaped the app boundary at Lcom/emmanuelmess/tictactoe/AndroidLauncher;.onCreate invoke_pc=0x1a depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/miniandroid/run/s44_sweep/tictactoe/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/miniandroid/run/s44_sweep/tictactoe/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260915-134444-2601`
- **Generated:** 2026-09-15 13:44:45 UTC
