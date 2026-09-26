# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/s107_apks/dev.cipher.notes.apk`
- **Package:** `dev.cipher.notes`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 22 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 17266 |
| `TraceEngine` | 3 |
| `Unknown` | 22 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 17232 |
| `Unknown.Unknown` | 22 |
| `ExecutionEngine.stage_capture_output` | 6 |
| `ExecutionEngine.trace_files` | 5 |
| `ExecutionEngine.stage_render_frame` | 4 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |
| `ExecutionEngine.execution_source` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.create_view_from_dalvik_result` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldev/cipher/notes/DaggerCipherApp_HiltComponents_SingletonC$Builder;.build invoke_pc=0x4 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldev/cipher/notes/Hilt_CipherApp$1;.get invoke_pc=0xf depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldev/cipher/notes/Hilt_CipherApp;.generatedComponent invoke_pc=0x4 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldev/cipher/notes/Hilt_CipherApp;.hiltInternalInject invoke_pc=0x7 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldev/cipher/notes/Hilt_CipherApp;.onCreate invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalStateException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldev/cipher/notes/DaggerCipherApp_HiltComponents_SingletonC$Builder;.build invoke_pc=0x4 depth=17
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldev/cipher/notes/Hilt_CipherApp$1;.get invoke_pc=0xf depth=16
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldev/cipher/notes/Hilt_CipherApp;.generatedComponent invoke_pc=0x4 depth=14
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldagger/hilt/EntryPoints;.get invoke_pc=0x28 depth=13
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldagger/hilt/android/EntryPointAccessors;.fromApplication invoke_pc=0x12 depth=12
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldagger/hilt/android/internal/managers/ActivityRetainedComponentManager$1;.create invoke_pc=0x9 depth=11
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/lifecycle/viewmodel/ViewModelProviderImpl_androidKt;.createViewModel invoke_pc=0xf depth=10
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/lifecycle/viewmodel/ViewModelProviderImpl;.getViewModel$lifecycle_viewmodel_release invoke_pc=0x3c depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/lifecycle/viewmodel/ViewModelProviderImpl;.getViewModel$lifecycle_viewmodel_release$default invoke_pc=0xa depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/lifecycle/ViewModelProvider;.get invoke_pc=0x9 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/lifecycle/ViewModelProvider;.get invoke_pc=0x9 depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldagger/hilt/android/internal/managers/ActivityRetainedComponentManager;.getSavedStateHandleHolder invoke_pc=0xa depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldagger/hilt/android/internal/managers/ActivityComponentManager;.getSavedStateHandleHolder invoke_pc=0x4 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldev/cipher/notes/Hilt_MainActivity;.initSavedStateHandleHolder invoke_pc=0xc depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldev/cipher/notes/Hilt_MainActivity;.onCreate invoke_pc=0x3 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalStateException; escaped the app boundary at Ldev/cipher/notes/MainActivity;.onCreate invoke_pc=0x9 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/dev.cipher.notes_run1/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/dev.cipher.notes_run1/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/dev.cipher.notes_run1/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/dev.cipher.notes_run1/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260926-171447-4593`
- **Generated:** 2026-09-26 17:14:49 UTC
