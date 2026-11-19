# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/upload/handoff_apks/com.minar.randomix_42.apk`
- **Package:** `com.minar.randomix`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 31 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 20 |
| Warnings | 32 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 1811 |
| `TraceEngine` | 3 |
| `Unknown` | 20 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 1716 |
| `ExecutionEngine.stage_render_frame` | 62 |
| `Unknown.Unknown` | 20 |
| `ExecutionEngine.stage_capture_output` | 7 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_initialize_runtime` | 3 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/fragment/app/q;.<init> invoke_pc=0x5e depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/navigation/fragment/NavHostFragment;.<init> invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lcom/minar/randomix/activities/MainActivity;.onCreate invoke_pc=0x1ac depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lgp;.k invoke_pc=0x1c depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lgp;.i invoke_pc=0x31 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lgp;.H invoke_pc=0x0 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lcom/google/android/material/card/MaterialCardView;.<init> invoke_pc=0x21 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalArgumentException; escaped the app boundary at Lcom/minar/randomix/activities/MainActivity;.onCreate invoke_pc=0x1ac depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lgp;.k invoke_pc=0x1c depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lgp;.i invoke_pc=0x31 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lgp;.H invoke_pc=0x0 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lcom/google/android/material/card/MaterialCardView;.<init> invoke_pc=0x21 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalArgumentException; escaped the app boundary at Lcom/minar/randomix/activities/MainActivity;.onCreate invoke_pc=0x1ac depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/fragment/app/q;.getParentFragmentManager invoke_pc=0xd depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Landroidx/navigation/fragment/NavHostFragment;.onAttach invoke_pc=0xa depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalStateException; escaped the app boundary at Lcom/minar/randomix/activities/MainActivity;.onCreate invoke_pc=0x46e depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lcom/minar/randomix/activities/MainActivity;.onCreate invoke_pc=0x46e depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lj4;.y invoke_pc=0x286 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lm3;.onPostCreate invoke_pc=0x9 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalStateException; escaped the app boundary at Lcom/minar/randomix/activities/MainActivity;.onCreate invoke_pc=0x46e depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `evidence/w20/runtime_perf/com.minar.randomix_42_r3/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](evidence/w20/runtime_perf/com.minar.randomix_42_r3/screenshot.png)

### Output Frame

- **File:** `evidence/w20/runtime_perf/com.minar.randomix_42_r3/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](evidence/w20/runtime_perf/com.minar.randomix_42_r3/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261119-114236-8031`
- **Generated:** 2026-11-19 11:42:41 UTC
