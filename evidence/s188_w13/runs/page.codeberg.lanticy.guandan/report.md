# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s188_w13/runs/store_page.codeberg.lanticy.guandan/data/app/page.codeberg.lanticy.guandan/base.apk`
- **Package:** `page.codeberg.lanticy.guandan`
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
| `ExecutionEngine` | 2796 |
| `TraceEngine` | 3 |
| `Unknown` | 32 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 2732 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lpage/codeberg/lanticy/guandan/net/NsdHelper;.<init> invoke_pc=0x14 depth=52
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lpage/codeberg/lanticy/guandan/net/GameController;.<init> invoke_pc=0xb0 depth=51
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/lifecycle/ViewModelProvider$AndroidViewModelFactory;.create invoke_pc=0x18 depth=50
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/lifecycle/ViewModelProvider$AndroidViewModelFactory;.create invoke_pc=0x4 depth=49
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/lifecycle/ViewModelProvider$AndroidViewModelFactory;.create invoke_pc=0x4 depth=48
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/lifecycle/SavedStateViewModelFactory;.create invoke_pc=0x3f depth=47
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/lifecycle/ViewModelProvider$Factory;.create invoke_pc=0x4 depth=46
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/ui/node/UiApplier;.getViewModel$lifecycle_viewmodel_release invoke_pc=0x48 depth=45
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlin/text/CharsKt;.RootScreen invoke_pc=0x11d depth=44
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lpage/codeberg/lanticy/guandan/ComposableSingletons$MainActivityKt$lambda-1$1;.invoke invoke_pc=0x19 depth=43
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/runtime/internal/ComposableLambdaImpl;.invoke invoke_pc=0x2e depth=42
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/runtime/AnchoredGroupPath;.CompositionLocalProvider invoke_pc=0xe2 depth=41
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/material3/TextKt;.ProvideTextStyle invoke_pc=0x4e depth=40
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/ui/node/NodeCoordinator$drawBlock$1;.invoke invoke_pc=0x2f4 depth=39
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/runtime/internal/ComposableLambdaImpl;.invoke invoke_pc=0x2e depth=38
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/runtime/AnchoredGroupPath;.CompositionLocalProvider invoke_pc=0x95 depth=37
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/material3/MaterialThemeKt;.MaterialTheme invoke_pc=0xcb depth=36
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lpage/codeberg/lanticy/guandan/MainActivity$onCreate$1;.invoke invoke_pc=0x2e depth=35
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/runtime/internal/ComposableLambdaImpl;.invoke invoke_pc=0x2e depth=34
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/runtime/AnchoredGroupPath;.CompositionLocalProvider invoke_pc=0x95 depth=33
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lpage/codeberg/lanticy/guandan/MainActivity$onCreate$1;.invoke invoke_pc=0x13d depth=32
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/runtime/internal/ComposableLambdaImpl;.invoke invoke_pc=0x2e depth=31
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/ui/platform/ComposeView;.Content invoke_pc=0x45 depth=30
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/ui/node/NodeCoordinator$drawBlock$1;.invoke invoke_pc=0xb2 depth=29
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/runtime/internal/ComposableLambdaImpl;.invoke invoke_pc=0x2e depth=28
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/runtime/AnchoredGroupPath;.CompositionLocalProvider invoke_pc=0x95 depth=27
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/ui/platform/CompositionLocalsKt;.ProvideCommonCompositionLocals invoke_pc=0x134 depth=26
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/foundation/gestures/ScrollableKt$semanticsScrollBy$2$1;.invoke invoke_pc=0x33 depth=25
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/runtime/internal/ComposableLambdaImpl;.invoke invoke_pc=0x2e depth=24
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/runtime/AnchoredGroupPath;.CompositionLocalProvider invoke_pc=0x95 depth=23
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/ui/platform/AndroidCompositionLocals_androidKt;.ProvideAndroidCompositionLocals invoke_pc=0x23f depth=22
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/compose/ui/platform/WrappedComposition$setContent$1$1;.invoke invoke_pc=0x24 depth=21
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s188_w13/runs/page.codeberg.lanticy.guandan/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s188_w13/runs/page.codeberg.lanticy.guandan/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s188_w13/runs/page.codeberg.lanticy.guandan/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s188_w13/runs/page.codeberg.lanticy.guandan/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261107-204216-8175`
- **Generated:** 2026-11-07 20:42:19 UTC
