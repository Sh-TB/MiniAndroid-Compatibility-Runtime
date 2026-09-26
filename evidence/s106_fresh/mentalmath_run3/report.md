# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s106_fresh/apks/mentalmath_27.apk`
- **Package:** `com.helddertierwelt.mentalmath`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 32 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 9196 |
| `TraceEngine` | 3 |
| `Unknown` | 32 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 9162 |
| `Unknown.Unknown` | 32 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/helddertierwelt/mentalmath/DaggerMentalMath_HiltComponents_SingletonC$Builder;.build invoke_pc=0x4 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/helddertierwelt/mentalmath/Hilt_MentalMath$1;.get invoke_pc=0xf depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/helddertierwelt/mentalmath/Hilt_MentalMath;.generatedComponent invoke_pc=0x4 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/helddertierwelt/mentalmath/Hilt_MentalMath;.hiltInternalInject invoke_pc=0x7 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/helddertierwelt/mentalmath/Hilt_MentalMath;.onCreate invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalStateException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/core/splashscreen/SplashScreen;.setKeepOnScreenCondition invoke_pc=0x7 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lcom/helddertierwelt/mentalmath/MainActivity;.onCreate invoke_pc=0xe depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/helddertierwelt/mentalmath/DaggerMentalMath_HiltComponents_SingletonC$Builder;.build invoke_pc=0x4 depth=17
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/helddertierwelt/mentalmath/Hilt_MentalMath$1;.get invoke_pc=0xf depth=16
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/helddertierwelt/mentalmath/Hilt_MentalMath;.generatedComponent invoke_pc=0x4 depth=14
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

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/lifecycle/viewmodel/internal/ViewModelProviderImpl_androidKt;.createViewModel invoke_pc=0xf depth=10
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/lifecycle/viewmodel/internal/ViewModelProviderImpl;.getViewModel$lifecycle_viewmodel$default invoke_pc=0xa depth=8
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

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Ldagger/hilt/android/internal/managers/ActivityComponentManager;.initSavedStateHandleHolders invoke_pc=0x4 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/helddertierwelt/mentalmath/Hilt_MainActivity;.initSavedStateHandleHolders invoke_pc=0x4 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/helddertierwelt/mentalmath/Hilt_MainActivity;.onCreate invoke_pc=0x3 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalStateException; escaped the app boundary at Lcom/helddertierwelt/mentalmath/MainActivity;.onCreate invoke_pc=0x11 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/lifecycle/LifecycleRegistry;.addObserver invoke_pc=0x7 depth=31
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/lifecycle/LifecycleCoroutineScopeImpl$register$1;.invokeSuspend invoke_pc=0x2c depth=30
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/internal/CoroutineExceptionHandlerImpl_commonKt;.handleUncaughtCoroutineException invoke_pc=0x2c depth=37
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/CoroutineExceptionHandlerKt;.handleCoroutineException invoke_pc=0x10 depth=36
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/StandaloneCoroutine;.handleJobException invoke_pc=0x4 depth=35
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/JobSupport;.finalizeFinishingState invoke_pc=0x71 depth=34
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/JobSupport;.tryMakeCompletingSlowPath invoke_pc=0xaf depth=33
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/JobSupport;.tryMakeCompleting invoke_pc=0x29 depth=32
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/JobSupport;.makeCompletingOnce$kotlinx_coroutines_core invoke_pc=0x4 depth=31
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s106_fresh/mentalmath_run3/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s106_fresh/mentalmath_run3/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s106_fresh/mentalmath_run3/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s106_fresh/mentalmath_run3/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260926-123030-3071`
- **Generated:** 2026-09-26 12:30:31 UTC
