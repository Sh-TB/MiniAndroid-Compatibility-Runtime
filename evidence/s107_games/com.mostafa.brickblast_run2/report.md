# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/s107_apks/com.mostafa.brickblast.apk`
- **Package:** `com.mostafa.brickblast`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 20 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 3950 |
| `TraceEngine` | 3 |
| `Unknown` | 20 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 3914 |
| `Unknown.Unknown` | 20 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lb4;.get invoke_pc=0x11 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/mostafa/brickblast/BrickBlastApplication;.a invoke_pc=0x9 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/mostafa/brickblast/BrickBlastApplication;.onCreate invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalStateException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Ldagger/hilt/android/internal/managers/ActivityRetainedComponentManager$1;.create invoke_pc=0x0 depth=17
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Lt82;.create invoke_pc=0x6 depth=16
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Ldagger/hilt/android/internal/managers/ActivityRetainedComponentManager$1;.create invoke_pc=0x0 depth=15
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Lv82;.a invoke_pc=0xe depth=13
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Ldagger/hilt/android/internal/managers/ActivityRetainedComponentManager;.createComponent invoke_pc=0x11 depth=12
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Ldagger/hilt/android/internal/managers/ActivityRetainedComponentManager;.generatedComponent invoke_pc=0x0 depth=10
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Ldagger/hilt/EntryPoints;.get invoke_pc=0x28 depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Ldagger/hilt/android/internal/managers/ActivityComponentManager;.createComponent invoke_pc=0x47 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Lcom/mostafa/brickblast/MainActivity;.generatedComponent invoke_pc=0x4 depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Lrc;.a invoke_pc=0xe depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Lvq;.onCreate invoke_pc=0x1e depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Lac0;.onCreate invoke_pc=0x0 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/UnsupportedOperationException; unwound Lcom/mostafa/brickblast/MainActivity;.o invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/UnsupportedOperationException; escaped the app boundary at Lcom/mostafa/brickblast/MainActivity;.onCreate invoke_pc=0x16 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Llq; unwound Lw2;.invokeSuspend invoke_pc=0x1d2 depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Llq; escaped the app boundary at Lcom/mostafa/brickblast/MainActivity;.onCreate invoke_pc=0x9d depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/com.mostafa.brickblast_run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/com.mostafa.brickblast_run2/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/com.mostafa.brickblast_run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/com.mostafa.brickblast_run2/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260926-163327-9800`
- **Generated:** 2026-09-26 16:33:28 UTC
