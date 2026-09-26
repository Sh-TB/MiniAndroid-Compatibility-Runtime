# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/s107_apks/paper.loop.apk`
- **Package:** `paper.loop`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 9 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 4504 |
| `TraceEngine` | 3 |
| `Unknown` | 9 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 4469 |
| `Unknown.Unknown` | 9 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/RuntimeException; unwound Lkotlin/jvm/internal/Intrinsics;.checkNotNull invoke_pc=0x2 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/RuntimeException; unwound Lpaper/loop/core/Haptics;.init invoke_pc=0x13 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/RuntimeException; unwound Lpaper/loop/App;.onCreate invoke_pc=0x11 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/RuntimeException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/SharedLibraryLoadRuntimeException; unwound Lcom/badlogic/gdx/utils/SharedLibraryLoader;.loadFile invoke_pc=0x0 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/SharedLibraryLoadRuntimeException; unwound Lcom/badlogic/gdx/backends/android/AndroidApplicationConfiguration$1;.load invoke_pc=0x0 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/SharedLibraryLoadRuntimeException; unwound Lcom/badlogic/gdx/backends/android/AndroidApplication;.init invoke_pc=0xa depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/SharedLibraryLoadRuntimeException; unwound Lcom/badlogic/gdx/backends/android/AndroidApplication;.initialize invoke_pc=0x1 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Lcom/badlogic/gdx/utils/SharedLibraryLoadRuntimeException; escaped the app boundary at Lpaper/loop/GameActivity;.onCreate invoke_pc=0x4c depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/paper.loop_run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/paper.loop_run2/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/paper.loop_run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/paper.loop_run2/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260926-163740-3293`
- **Generated:** 2026-09-26 16:37:40 UTC
