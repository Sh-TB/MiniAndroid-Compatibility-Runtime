# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/s107_apks/com.vsmartcard.acardemulator.apk`
- **Package:** `com.vsmartcard.acardemulator`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 26 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 7201 |
| `TraceEngine` | 3 |
| `Unknown` | 26 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 7165 |
| `Unknown.Unknown` | 26 |
| `ExecutionEngine.stage_capture_output` | 6 |
| `ExecutionEngine.trace_files` | 5 |
| `ExecutionEngine.stage_render_frame` | 4 |
| `ExecutionEngine.phase_b_click` | 3 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |
| `ExecutionEngine.execution_source` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.create_view_from_dalvik_result` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/coordinatorlayout/widget/CoordinatorLayout;.prepareChildren invoke_pc=0x16 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/coordinatorlayout/widget/CoordinatorLayout;.onMeasure invoke_pc=0x2 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lcom/vsmartcard/acardemulator/MainActivity;.onCreate invoke_pc=0x6 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/core/view/WindowInsetsCompat$Impl28;.consumeDisplayCutout invoke_pc=0x2 depth=18
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/core/view/WindowInsetsCompat;.consumeDisplayCutout invoke_pc=0x2 depth=17
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/core/view/WindowInsetsCompat$Impl;.<clinit> invoke_pc=0x9 depth=16
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/core/view/WindowInsetsCompat;.<init> invoke_pc=0x6f depth=15
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/core/view/WindowInsetsCompat$BuilderImpl;.<init> invoke_pc=0x6 depth=14
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/core/view/WindowInsetsCompat$BuilderImpl29;.<init> invoke_pc=0x0 depth=13
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/core/view/WindowInsetsCompat$BuilderImpl30;.<init> invoke_pc=0x0 depth=12
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/core/view/WindowInsetsCompat$Builder;.<init> invoke_pc=0xb depth=11
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/ActionBarOverlayLayout;.<clinit> invoke_pc=0xd depth=10
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/ActionBarOverlayLayout;.init invoke_pc=0x8 depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/ActionBarOverlayLayout;.<init> invoke_pc=0x63 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/app/AppCompatDelegateImpl;.createSubDecor invoke_pc=0x9f depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/Toolbar;.inflateMenu invoke_pc=0x8 depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/Toolbar;.<init> invoke_pc=0x1a2 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/app/AppCompatDelegateImpl;.createSubDecor invoke_pc=0x9f depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/core/view/WindowInsetsCompat$Impl29;.inset invoke_pc=0x2 depth=10
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/core/view/WindowInsetsCompat;.inset invoke_pc=0x2 depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/ActionBarOverlayLayout;.onMeasure invoke_pc=0x97 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/app/AppCompatDelegateImpl;.createSubDecor invoke_pc=0x9f depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/Toolbar;.onMeasure invoke_pc=0xbe depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/app/AppCompatDelegateImpl;.createSubDecor invoke_pc=0x9f depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/appcompat/app/AppCompatActivity;.setSupportActionBar invoke_pc=0x4 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalStateException; escaped the app boundary at Lcom/vsmartcard/acardemulator/MainActivity;.onCreate invoke_pc=0x12 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/com.vsmartcard.acardemulator_run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/com.vsmartcard.acardemulator_run2/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/com.vsmartcard.acardemulator_run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/com.vsmartcard.acardemulator_run2/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260926-174844-2818`
- **Generated:** 2026-09-26 17:48:45 UTC
