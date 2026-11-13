# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s188_w13/runs/store_com.astroloop.game/data/app/com.astroloop.game/base.apk`
- **Package:** `com.astroloop.game`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 15 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 15 |
| Warnings | 16 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 1266 |
| `TraceEngine` | 3 |
| `Unknown` | 15 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 1203 |
| `ExecutionEngine.stage_render_frame` | 30 |
| `Unknown.Unknown` | 15 |
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

- **Message:** [EXC-UNWIND] Landroid/content/res/Resources$NotFoundException; unwound Lp/l;.a invoke_pc=0x12 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Landroid/content/res/Resources$NotFoundException; unwound Lcom/astroloop/game/render/FontManager;.initialize invoke_pc=0xd depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Landroid/content/res/Resources$NotFoundException; escaped the app boundary at Lcom/astroloop/game/MainActivity;.onCreate invoke_pc=0x3f depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/astroloop/game/hangar/HangarState;.<init> invoke_pc=0x4a depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/astroloop/game/hangar/HangarSurfaceView;.<init> invoke_pc=0x1f depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/astroloop/game/MainActivity;.showHangar invoke_pc=0x11 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lcom/astroloop/game/MainActivity;.onCreate invoke_pc=0x96 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/SavedStateHandleAttacher;.c invoke_pc=0x20 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/t;.a invoke_pc=0x16 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/u;.g invoke_pc=0x16e depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/u;.f invoke_pc=0x44 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/u;.e invoke_pc=0xe depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/A;.a invoke_pc=0x15 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/C$a;.onActivityPostCreated invoke_pc=0x9 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalArgumentException; escaped the app boundary at Lcom/astroloop/game/MainActivity;.onCreate invoke_pc=0x9d depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s188_w13/runs/com.astroloop.game/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s188_w13/runs/com.astroloop.game/screenshot.png)
- **SHA256:** `31ddd4d5b8e6d18e4a14cd38a44bd355b4e809de97f3f97bcd669ac103838093` (recorded by tools/report_sanity_fix.py from the actual retained file)

## Session Info

- **Session ID:** `EXP-001-20261107-203101-9706`
- Run id: `EXP-001-20261107-203101-9706` (derived from the report\'s own Session ID line)
- **Generated:** 2026-11-07 20:31:03 UTC
