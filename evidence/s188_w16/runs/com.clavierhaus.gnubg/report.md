# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s188_w16/runs/store_com.clavierhaus.gnubg/data/app/com.clavierhaus.gnubg/base.apk`
- **Package:** `com.clavierhaus.gnubg`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 15 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 22 |
| Warnings | 1 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 9377 |
| `TraceEngine` | 3 |
| `Unknown` | 22 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 9312 |
| `ExecutionEngine.stage_render_frame` | 30 |
| `Unknown.Unknown` | 22 |
| `ExecutionEngine.stage_capture_output` | 7 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
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

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/FlowKt__ChannelsKt;.access$emitAllImpl$FlowKt__ChannelsKt invoke_pc=0x0 depth=146
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/FlowKt__ChannelsKt$emitAllImpl$1;.invokeSuspend invoke_pc=0xd depth=145
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/internal/ChannelFlow$collect$2;.invokeSuspend invoke_pc=0xb depth=145
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/SharedFlowImpl$collect$1;.invokeSuspend invoke_pc=0xe depth=145
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Landroidx/datastore/core/DataStoreImpl$data$1$updateCollector$1;.invokeSuspend invoke_pc=0x13 depth=145
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/JobKt;.ensureActive invoke_pc=0x0 depth=118
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/FlowKt__LimitKt$takeWhile$$inlined$unsafeFlow$1;.collect invoke_pc=0x59 depth=116
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/FlowKt__LimitKt$dropWhile$$inlined$unsafeFlow$1;.collect invoke_pc=0x10 depth=115
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Landroidx/datastore/core/DataStoreImpl$internalDataFlow$1$invokeSuspend$$inlined$map$1;.collect invoke_pc=0x9 depth=114
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/FlowKt__CollectKt;.emitAll invoke_pc=0x3 depth=113
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/FlowKt;.emitAll invoke_pc=0x0 depth=112
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Landroidx/datastore/core/DataStoreImpl$internalDataFlow$1;.invokeSuspend invoke_pc=0xb0 depth=111
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Landroidx/datastore/core/DataStoreImpl$internalDataFlow$1;.invoke invoke_pc=0x8 depth=110
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Landroidx/datastore/core/DataStoreImpl$internalDataFlow$1;.invoke invoke_pc=0x4 depth=109
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/SafeFlow;.collectSafely invoke_pc=0x2 depth=108
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/FlowKt__EmittersKt$onStart$$inlined$unsafeFlow$1;.collect invoke_pc=0x77 depth=106
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Landroidx/datastore/core/DataStoreImpl$data$1;.invokeSuspend invoke_pc=0x5d depth=104
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Landroidx/datastore/core/DataStoreImpl$data$1;.invoke invoke_pc=0x8 depth=103
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Landroidx/datastore/core/DataStoreImpl$data$1;.invoke invoke_pc=0x4 depth=102
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/ChannelFlowBuilder;.collectTo$suspendImpl invoke_pc=0x2 depth=101
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/ChannelFlowBuilder;.collectTo invoke_pc=0x0 depth=100
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/internal/ChannelFlow$collectToFun$1;.invokeSuspend invoke_pc=0x25 depth=99
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s188_w16/runs/com.clavierhaus.gnubg/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s188_w16/runs/com.clavierhaus.gnubg/screenshot.png)
- **SHA256:** `b5a7a35d5fe0564b08842f187f4e293bbb1d1b63099ba43978542449ae8c1f5b` (recorded by tools/report_sanity_fix.py from the actual retained file)

## Session Info

- **Session ID:** `EXP-001-20261108-050127-1345`
- Run id: `EXP-001-20261108-050127-1345` (derived from the report\'s own Session ID line)
- **Generated:** 2026-11-08 05:01:35 UTC
