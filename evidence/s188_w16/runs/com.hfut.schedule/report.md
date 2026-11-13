# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s188_w16/runs/store_com.hfut.schedule/data/app/com.hfut.schedule/base.apk`
- **Package:** `com.hfut.schedule`
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
| `ExecutionEngine` | 5809 |
| `TraceEngine` | 3 |
| `Unknown` | 32 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 5746 |
| `Unknown.Unknown` | 32 |
| `ExecutionEngine.stage_render_frame` | 30 |
| `ExecutionEngine.stage_capture_output` | 7 |
| `ExecutionEngine.trace_files` | 5 |
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
| `ExecutionEngine.stage_frame_sequence` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/hfut/schedule/logic/util/sys/datetime/DateTimeManager;.<clinit> invoke_pc=0x94 depth=26
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/hfut/schedule/application/MyApplication$onCreate$1;.invokeSuspend invoke_pc=0x30 depth=25
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/internal/SafeCollectorKt$emitFun$1;.invoke invoke_pc=0x0 depth=62
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/internal/SafeCollectorKt$emitFun$1;.invoke invoke_pc=0x4 depth=61
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/internal/SafeCollector;.emit invoke_pc=0x27 depth=60
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Landroidx/datastore/core/DataStoreImpl$data$1;.invokeSuspend invoke_pc=0x64 depth=58
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Landroidx/datastore/core/DataStoreImpl$data$1;.invoke invoke_pc=0x8 depth=57
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Landroidx/datastore/core/DataStoreImpl$data$1;.invoke invoke_pc=0x4 depth=56
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlinx/coroutines/flow/internal/AbortFlowException; unwound Lkotlinx/coroutines/flow/SafeFlow;.collectSafely invoke_pc=0x2 depth=55
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/glance/appwidget/GlanceAppWidgetManager;.getState invoke_pc=0x77 depth=51
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/glance/appwidget/GlanceAppWidgetManager;.getGlanceIds invoke_pc=0x43 depth=50
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/hfut/schedule/receiver/widget/focus/FocusWidgetReceiverKt$hasFocusWidget$2;.invokeSuspend invoke_pc=0x28 depth=49
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/jsoup/helper/ValidationException; unwound Lorg/jsoup/parser/CharacterReader;.<init> invoke_pc=0x19 depth=88
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/jsoup/helper/ValidationException; unwound Lorg/jsoup/parser/CharacterReader;.<init> invoke_pc=0x9 depth=87
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/jsoup/helper/ValidationException; unwound Lorg/jsoup/nodes/Entities;.load invoke_pc=0x16 depth=86
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/jsoup/helper/ValidationException; unwound Lorg/jsoup/nodes/Entities;.access$000 invoke_pc=0x0 depth=85
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/jsoup/helper/ValidationException; unwound Lorg/jsoup/nodes/Entities$EscapeMode;.<init> invoke_pc=0x3 depth=84
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/jsoup/helper/ValidationException; unwound Lorg/jsoup/nodes/Entities$EscapeMode;.<clinit> invoke_pc=0x9 depth=83
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/jsoup/helper/ValidationException; unwound Lorg/jsoup/nodes/Document$OutputSettings;.<init> invoke_pc=0x3 depth=82
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/jsoup/helper/ValidationException; unwound Lorg/jsoup/nodes/Document;.<init> invoke_pc=0xd depth=81
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/jsoup/helper/ValidationException; unwound Lorg/jsoup/parser/TreeBuilder;.initialiseParse invoke_pc=0x13 depth=80
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/jsoup/helper/ValidationException; unwound Lorg/jsoup/parser/HtmlTreeBuilder;.initialiseParse invoke_pc=0x0 depth=79
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/jsoup/helper/ValidationException; unwound Lorg/jsoup/parser/TreeBuilder;.parse invoke_pc=0x0 depth=78
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/jsoup/helper/ValidationException; unwound Lorg/jsoup/parser/Parser;.parse invoke_pc=0xf depth=77
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/jsoup/helper/ValidationException; unwound Lorg/jsoup/Jsoup;.parse invoke_pc=0x2 depth=76
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlin/jvm/internal/Intrinsics;.checkNotNullParameter invoke_pc=0x2 depth=82
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/xah/common/logic/util/LogUtil$ErrorEntry;.<init> invoke_pc=0x7 depth=81
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/xah/common/logic/util/LogUtil$ErrorEntry;.<init> invoke_pc=0x8 depth=80
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/xah/common/logic/util/LogUtil;.baseLog invoke_pc=0x6d depth=78
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/xah/common/logic/util/LogUtil;.error invoke_pc=0xc depth=77
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/xah/common/logic/util/LogUtil;.error$default invoke_pc=0x6 depth=76
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/hfut/schedule/ui/screen/home/search/function/jxglstu/person/PersonItemsKt;.getPersonInfo invoke_pc=0x2ce depth=75
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s188_w16/runs/com.hfut.schedule/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s188_w16/runs/com.hfut.schedule/screenshot.png)
- **SHA256:** `d602648e8e401895b7b440bc9c0becd4af8748b37808ce0870735b19502dab71` (recorded by tools/report_sanity_fix.py from the actual retained file)

## Session Info

- **Session ID:** `EXP-001-20261108-050207-8553`
- Run id: `EXP-001-20261108-050207-8553` (derived from the report\'s own Session ID line)
- **Generated:** 2026-11-08 05:02:30 UTC
