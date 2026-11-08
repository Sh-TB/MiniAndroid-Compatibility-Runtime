# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s188_w16/runs/store_de.taz.android.app.free/data/app/de.taz.android.app.free/base.apk`
- **Package:** `de.taz.android.app.free`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 15 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 32 |
| Warnings | 1 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 6553 |
| `TraceEngine` | 3 |
| `Unknown` | 32 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 6489 |
| `Unknown.Unknown` | 32 |
| `ExecutionEngine.stage_render_frame` | 30 |
| `ExecutionEngine.stage_capture_output` | 7 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
| `ExecutionEngine.stage_frame_sequence` | 1 |
| `TraceEngine.start_session` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/DistinctFlowImpl$collect$2;.emit invoke_pc=0x75 depth=48
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lde/taz/app/android/dataStore/SimpleDataStoreEntry$asFlow$$inlined$map$1$2;.emit invoke_pc=0xf8 depth=47
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/internal/SafeCollectorKt$emitFun$1;.invoke invoke_pc=0x0 depth=46
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/internal/SafeCollectorKt$emitFun$1;.invoke invoke_pc=0x4 depth=45
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/internal/SafeCollector;.emit invoke_pc=0x25 depth=44
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Landroidx/datastore/core/DataStoreImpl$data$1;.invokeSuspend invoke_pc=0x64 depth=42
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Landroidx/datastore/core/DataStoreImpl$data$1;.invoke invoke_pc=0x8 depth=41
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Landroidx/datastore/core/DataStoreImpl$data$1;.invoke invoke_pc=0x4 depth=40
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/SafeFlow;.collectSafely invoke_pc=0x2 depth=39
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lde/taz/app/android/dataStore/SimpleDataStoreEntry$asFlow$$inlined$map$1;.collect invoke_pc=0xb depth=37
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/DistinctFlowImpl;.collect invoke_pc=0x12 depth=36
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/FileWriteScope$writeData$2;.invoke invoke_pc=0x8 depth=58
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/FileWriteScope$writeData$2;.invoke invoke_pc=0x2 depth=57
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/FileStorageKt;.runFileDiagnosticsIfNotCorruption invoke_pc=0x3d depth=56
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/FileStorageKt;.access$runFileDiagnosticsIfNotCorruption invoke_pc=0x0 depth=55
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/FileWriteScope;.writeData invoke_pc=0xf depth=54
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/DataStoreImpl$writeData$2;.invokeSuspend invoke_pc=0x5c depth=53
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/DataStoreImpl$writeData$2;.invoke invoke_pc=0x8 depth=52
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/DataStoreImpl$writeData$2;.invoke invoke_pc=0x4 depth=51
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/DataStoreImpl;.writeData$datastore_core invoke_pc=0x51 depth=49
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/DataStoreImpl$transformAndWrite$2;.invokeSuspend invoke_pc=0x6f depth=48
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/DataStoreImpl$transformAndWrite$2;.invoke invoke_pc=0x8 depth=47
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/DataStoreImpl$transformAndWrite$2;.invoke invoke_pc=0x2 depth=46
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/DataStoreImpl;.transformAndWrite invoke_pc=0xc depth=44
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/DataStoreImpl;.access$transformAndWrite invoke_pc=0x0 depth=43
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/DataStoreImpl$handleUpdate$2$1;.invokeSuspend invoke_pc=0x4a depth=42
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/DataStoreImpl$handleUpdate$2$1;.invoke invoke_pc=0x8 depth=41
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/DataStoreImpl$handleUpdate$2$1;.invoke invoke_pc=0x4 depth=40
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/intrinsics/UndispatchedKt;.startUndispatchedOrReturn invoke_pc=0x1 depth=38
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/BuildersKt;.withContext invoke_pc=0x0 depth=36
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/datastore/core/DataStoreImpl$updateData$2;.invokeSuspend invoke_pc=0xb depth=30
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lde/taz/app/android/AbstractTazApplication;.generateInstallationId invoke_pc=0x32 depth=35
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s188_w16/runs/de.taz.android.app.free/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s188_w16/runs/de.taz.android.app.free/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s188_w16/runs/de.taz.android.app.free/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s188_w16/runs/de.taz.android.app.free/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261108-050257-7860`
- **Generated:** 2026-11-08 05:03:09 UTC
