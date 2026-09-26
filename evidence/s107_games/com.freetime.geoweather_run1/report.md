# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/s107_apks/com.freetime.geoweather.apk`
- **Package:** `com.freetime.geoweather`
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
| `ExecutionEngine` | 17338 |
| `TraceEngine` | 3 |
| `Unknown` | 32 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 17304 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lio/ktor/client/HttpClientJvmKt;.HttpClient invoke_pc=0x5 depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/freetime/geoweather/data/WeatherApiClient;.<init> invoke_pc=0x9 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/freetime/geoweather/data/DependencyManager;.initialize invoke_pc=0x1c depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/freetime/geoweather/GeoWeatherApp;.initDependencies invoke_pc=0x20 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lcom/freetime/geoweather/GeoWeatherApp;.onCreate invoke_pc=0x9 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalStateException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/lifecycle/LifecycleRegistry;.addObserver invoke_pc=0x7 depth=33
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/activity/ComponentActivity;.addObserverForBackInvoker invoke_pc=0xb depth=32
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/activity/ComponentActivity;.onBackPressedDispatcher_delegate$lambda$0$1$0 invoke_pc=0x0 depth=31
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/activity/ComponentActivity;.$r8$lambda$7IJBVrN0sHyidCAZufWEJFc7-yY invoke_pc=0x0 depth=30
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/activity/ComponentActivity$$ExternalSyntheticLambda1;.run invoke_pc=0x4 depth=29
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/scheduling/CoroutineScheduler$Worker;.park invoke_pc=0x17 depth=28
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/scheduling/CoroutineScheduler$Worker;.tryPark invoke_pc=0x3b depth=27
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/scheduling/CoroutineScheduler$Worker;.runWorker invoke_pc=0x3c depth=26
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/scheduling/CoroutineScheduler$Worker;.run invoke_pc=0x0 depth=25
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/scheduling/CoroutineScheduler;.createNewWorker invoke_pc=0x66 depth=24
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/scheduling/CoroutineScheduler;.tryCreateWorker invoke_pc=0x19 depth=23
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/scheduling/CoroutineScheduler;.tryCreateWorker$default invoke_pc=0xc depth=22
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/scheduling/CoroutineScheduler;.signalCpuWork invoke_pc=0xb depth=21
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/scheduling/CoroutineScheduler;.dispatch invoke_pc=0x51 depth=20
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/scheduling/CoroutineScheduler;.dispatch$default invoke_pc=0xb depth=19
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/scheduling/SchedulerCoroutineDispatcher;.dispatch invoke_pc=0x7 depth=18
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/DispatchException; unwound Lkotlinx/coroutines/internal/DispatchedContinuationKt;.resumeCancellableWithInternal invoke_pc=0x23 depth=16
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/intrinsics/CancellableKt;.startCoroutineCancellable invoke_pc=0x15 depth=15
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/CoroutineStart;.invoke invoke_pc=0x23 depth=14
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/AbstractCoroutine;.start invoke_pc=0x2 depth=13
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/BuildersKt__Builders_commonKt;.launch invoke_pc=0x18 depth=12
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/BuildersKt;.launch invoke_pc=0x0 depth=11
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/BuildersKt__Builders_commonKt;.launch$default invoke_pc=0xe depth=10
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/BuildersKt;.launch$default invoke_pc=0x0 depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/compose/ui/platform/GlobalSnapshotManager;.ensureStarted invoke_pc=0x26 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/compose/ui/platform/Wrapper_androidKt;.setContent invoke_pc=0x2 depth=7
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/com.freetime.geoweather_run1/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/com.freetime.geoweather_run1/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/com.freetime.geoweather_run1/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/com.freetime.geoweather_run1/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260926-172035-0054`
- **Generated:** 2026-09-26 17:20:37 UTC
