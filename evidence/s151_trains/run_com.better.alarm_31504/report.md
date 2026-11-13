# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s151_trains/store_com.better.alarm_31504/data/data/app/com.better.alarm/base.apk`
- **Package:** `com.better.alarm`
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
| `ExecutionEngine` | 6968 |
| `TraceEngine` | 3 |
| `Unknown` | 32 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 6930 |
| `Unknown.Unknown` | 32 |
| `ExecutionEngine.stage_capture_output` | 8 |
| `ExecutionEngine.trace_files` | 5 |
| `ExecutionEngine.stage_render_frame` | 4 |
| `DalvikEngine.execute_apk` | 3 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.phase_b_click` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `TraceEngine.start_session` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |
| `ExecutionEngine.execution_source` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IndexOutOfBoundsException; unwound Lorg/koin/core/module/ModuleKt;.flatten$default invoke_pc=0x8 depth=14
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IndexOutOfBoundsException; unwound Lorg/koin/core/Koin;.loadModules invoke_pc=0x7 depth=13
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IndexOutOfBoundsException; unwound Lorg/koin/core/KoinApplication;.loadModules invoke_pc=0x4 depth=12
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IndexOutOfBoundsException; unwound Lorg/koin/core/KoinApplication;.modules invoke_pc=0x76 depth=11
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IndexOutOfBoundsException; unwound Lorg/koin/core/KoinApplication;.modules invoke_pc=0x9 depth=10
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IndexOutOfBoundsException; unwound Lcom/better/alarm/configuration/ContainerKt$startKoin$1;.invoke invoke_pc=0x7 depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IndexOutOfBoundsException; unwound Lcom/better/alarm/configuration/ContainerKt$startKoin$1;.invoke invoke_pc=0x2 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IndexOutOfBoundsException; unwound Lorg/koin/core/context/DefaultContextExtKt;.startKoin invoke_pc=0xb depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IndexOutOfBoundsException; unwound Lcom/better/alarm/configuration/ContainerKt;.startKoin invoke_pc=0x1a depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IndexOutOfBoundsException; unwound Lcom/better/alarm/configuration/AlarmApplicationInit;.startOnce invoke_pc=0x40 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IndexOutOfBoundsException; unwound Lcom/better/alarm/configuration/AlarmApplication$Companion;.startOnce invoke_pc=0x7 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IndexOutOfBoundsException; unwound Lcom/better/alarm/configuration/AlarmApplication;.onCreate invoke_pc=0x5 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IndexOutOfBoundsException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/koin/core/error/NoBeanDefFoundException; unwound Lorg/koin/core/scope/Scope;.resolveValue invoke_pc=0xf9 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/koin/core/error/NoBeanDefFoundException; unwound Lorg/koin/core/scope/Scope;.resolveInstance invoke_pc=0x4e depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/koin/core/error/NoBeanDefFoundException; unwound Lorg/koin/core/scope/Scope;.get invoke_pc=0xa1 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/koin/core/error/NoBeanDefFoundException; unwound Lcom/better/alarm/presenter/AlarmsListActivity$special$$inlined$globalInject$default$5;.invoke invoke_pc=0x18 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/koin/core/error/NoBeanDefFoundException; unwound Lcom/better/alarm/presenter/AlarmsListActivity;.getDynamicThemeHandler invoke_pc=0x2 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Lorg/koin/core/error/NoBeanDefFoundException; escaped the app boundary at Lcom/better/alarm/presenter/AlarmsListActivity;.onCreate invoke_pc=0xe depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lcom/better/alarm/presenter/AlarmsListActivity;.onCreate invoke_pc=0x14 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/koin/core/error/NoBeanDefFoundException; unwound Lorg/koin/core/scope/Scope;.resolveValue invoke_pc=0xf9 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/koin/core/error/NoBeanDefFoundException; unwound Lorg/koin/core/scope/Scope;.resolveInstance invoke_pc=0x4e depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/koin/core/error/NoBeanDefFoundException; unwound Lorg/koin/core/scope/Scope;.get invoke_pc=0xa1 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/koin/core/error/NoBeanDefFoundException; unwound Lcom/better/alarm/presenter/AlarmsListActivity$special$$inlined$globalInject$default$4;.invoke invoke_pc=0x18 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/koin/core/error/NoBeanDefFoundException; unwound Lcom/better/alarm/presenter/AlarmsListActivity;.getUiStore invoke_pc=0x2 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Lorg/koin/core/error/NoBeanDefFoundException; escaped the app boundary at Lcom/better/alarm/presenter/AlarmsListActivity;.onCreate invoke_pc=0x1e depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Landroid/content/res/Resources$NotFoundException; unwound Landroidx/core/content/res/ResourcesCompat;.getColorStateList invoke_pc=0xc depth=10
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Landroid/content/res/Resources$NotFoundException; unwound Landroidx/core/content/ContextCompat;.getColorStateList invoke_pc=0x8 depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Landroid/content/res/Resources$NotFoundException; unwound Landroidx/appcompat/content/res/AppCompatResources;.getColorStateList invoke_pc=0x0 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Landroid/content/res/Resources$NotFoundException; unwound Landroidx/appcompat/widget/TintTypedArray;.getColorStateList invoke_pc=0x13 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Landroid/content/res/Resources$NotFoundException; unwound Landroidx/appcompat/widget/Toolbar;.<init> invoke_pc=0x17c depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Landroid/content/res/Resources$NotFoundException; unwound Landroidx/appcompat/app/AppCompatDelegateImpl;.createSubDecor invoke_pc=0x9f depth=5
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s151_trains/run_com.better.alarm_31504/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s151_trains/run_com.better.alarm_31504/screenshot.png)
- **SHA256:** `0bd24c912042a6c1818a4a3c1b6c8d666614198c37b369c77676fb976540e50d` (recorded by tools/report_sanity_fix.py from the actual retained file)

## Session Info

- **Session ID:** `EXP-001-20261102-161757-8535`
- **Generated:** 2026-11-02 16:17:58 UTC
