# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s188_w16/runs/store_site.leos.apps.lespas/data/app/site.leos.apps.lespas/base.apk`
- **Package:** `site.leos.apps.lespas`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 15 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 13 |
| Warnings | 1 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 7441 |
| `TraceEngine` | 3 |
| `Unknown` | 13 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 7378 |
| `ExecutionEngine.stage_render_frame` | 30 |
| `Unknown.Unknown` | 13 |
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

- **Message:** [EXC-UNWIND] Lkotlin/UninitializedPropertyAccessException; unwound Lkotlin/jvm/internal/Intrinsics;.throwUninitializedPropertyAccessException invoke_pc=0x13 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lkotlin/UninitializedPropertyAccessException; unwound Lcom/google/android/apps/muzei/api/provider/MuzeiArtProvider;.attachInfo invoke_pc=0x18 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Lkotlin/UninitializedPropertyAccessException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/google/android/apps/muzei/api/provider/MuzeiArtProvider$contentUri$2;.invoke invoke_pc=0xe depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/google/android/apps/muzei/api/provider/MuzeiArtProvider$contentUri$2;.invoke invoke_pc=0x0 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/google/android/apps/muzei/api/provider/MuzeiArtProvider;.getContentUri invoke_pc=0x2 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/google/android/apps/muzei/api/provider/MuzeiArtProvider;.onCreate invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/startup/InitializationProvider;.onCreate invoke_pc=0x14 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/fragment/app/BackStackRecord;.commitInternal invoke_pc=0x47 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/fragment/app/BackStackRecord;.commit invoke_pc=0x2 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalStateException; escaped the app boundary at Lsite/leos/apps/lespas/MainActivity;.onCreate invoke_pc=0x82 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s188_w16/runs/site.leos.apps.lespas/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s188_w16/runs/site.leos.apps.lespas/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s188_w16/runs/site.leos.apps.lespas/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s188_w16/runs/site.leos.apps.lespas/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261108-050344-3810`
- **Generated:** 2026-11-08 05:03:50 UTC
