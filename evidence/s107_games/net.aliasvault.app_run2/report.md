# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/s107_apks/net.aliasvault.app.apk`
- **Package:** `net.aliasvault.app`
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
| `ExecutionEngine` | 8985 |
| `TraceEngine` | 3 |
| `Unknown` | 32 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 8949 |
| `Unknown.Unknown` | 32 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/facebook/soloader/recovery/DefaultRecoveryStrategyFactory;.<init> invoke_pc=0x15 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/facebook/soloader/SoLoader;.init invoke_pc=0x1 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/facebook/soloader/SoLoader;.init invoke_pc=0x7 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/facebook/react/ReactNativeApplicationEntryPoint;.loadReactNative invoke_pc=0x2 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lnet/aliasvault/app/MainApplication;.onCreate invoke_pc=0x1f depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/RuntimeException; unwound Lkotlin/jvm/internal/Intrinsics;.checkNotNull invoke_pc=0x2 depth=11
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lnet/aliasvault/app/MainActivity;.onCreate invoke_pc=0x5 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lexpo/modules/ReactActivityDelegateWrapper$onCreate$2;.invokeSuspend invoke_pc=0x41 depth=17
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lexpo/modules/ReactActivityDelegateWrapper$onCreate$2;.invoke invoke_pc=0x8 depth=16
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lexpo/modules/ReactActivityDelegateWrapper$onCreate$2;.invoke invoke_pc=0x4 depth=15
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lexpo/modules/ReactActivityDelegateWrapper$launchLifecycleScopeWithLock$1;.invoke invoke_pc=0x8 depth=13
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lexpo/modules/ReactActivityDelegateWrapper$launchLifecycleScopeWithLock$1;.invoke invoke_pc=0x4 depth=12
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/internal/CoroutineExceptionHandlerImpl_commonKt;.handleUncaughtCoroutineException invoke_pc=0x2c depth=19
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/CoroutineExceptionHandlerKt;.handleCoroutineException invoke_pc=0x1a depth=18
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/StandaloneCoroutine;.handleJobException invoke_pc=0x4 depth=17
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/JobSupport;.finalizeFinishingState invoke_pc=0x71 depth=16
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/JobSupport;.tryMakeCompletingSlowPath invoke_pc=0xaf depth=15
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/JobSupport;.tryMakeCompleting invoke_pc=0x29 depth=14
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/JobSupport;.makeCompletingOnce$kotlinx_coroutines_core invoke_pc=0x4 depth=13
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/AbstractCoroutine;.resumeWith invoke_pc=0x4 depth=12
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/intrinsics/UndispatchedKt;.startCoroutineUndispatched invoke_pc=0x51 depth=11
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/CoroutineStart;.invoke invoke_pc=0x1b depth=10
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/AbstractCoroutine;.start invoke_pc=0x2 depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/BuildersKt__Builders_commonKt;.launch invoke_pc=0x18 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/BuildersKt;.launch invoke_pc=0x0 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/BuildersKt__Builders_commonKt;.launch$default invoke_pc=0xe depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/BuildersKt;.launch$default invoke_pc=0x0 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lexpo/modules/ReactActivityDelegateWrapper;.launchLifecycleScopeWithLock invoke_pc=0x17 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lexpo/modules/ReactActivityDelegateWrapper;.onCreate invoke_pc=0x6e depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/facebook/react/ReactActivity;.onCreate invoke_pc=0x5 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lnet/aliasvault/app/MainActivity;.onCreate invoke_pc=0x9 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/net.aliasvault.app_run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/net.aliasvault.app_run2/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/net.aliasvault.app_run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/net.aliasvault.app_run2/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260926-174010-0917`
- **Generated:** 2026-09-26 17:40:13 UTC
