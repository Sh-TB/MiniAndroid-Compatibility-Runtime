# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/upload/handoff_apks/org.ecos.logic.flip_a_coin_3.apk`
- **Package:** `org.ecos.logic.flip_a_coin`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 11 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 15 |
| Warnings | 1 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 6812 |
| `TraceEngine` | 3 |
| `Unknown` | 15 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 6756 |
| `ExecutionEngine.stage_render_frame` | 22 |
| `Unknown.Unknown` | 15 |
| `ExecutionEngine.stage_capture_output` | 7 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_initialize_runtime` | 3 |
| `ExecutionEngine.create_view_from_dalvik_result` | 2 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `TraceEngine.start_session` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.stage_frame_sequence` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/ViewModelProvider;.get invoke_pc=0x3e depth=16
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/SavedStateHandleSupport;.getSavedStateHandlesVM invoke_pc=0x24 depth=15
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/SavedStateHandlesProvider$viewModel$2;.invoke invoke_pc=0x2 depth=14
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/SavedStateHandlesProvider$viewModel$2;.invoke invoke_pc=0x0 depth=13
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/SavedStateHandlesProvider;.getViewModel invoke_pc=0x2 depth=11
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/SavedStateHandlesProvider;.performRestore invoke_pc=0x11 depth=10
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/SavedStateHandleAttacher;.onStateChanged invoke_pc=0x1a depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/LifecycleRegistry$ObserverWithState;.dispatchEvent invoke_pc=0x18 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/LifecycleRegistry;.forwardPass invoke_pc=0x56 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/LifecycleRegistry;.sync invoke_pc=0x53 depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/LifecycleRegistry;.moveToState invoke_pc=0x44 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/LifecycleRegistry;.handleLifecycleEvent invoke_pc=0xe depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/ReportFragment$Companion;.dispatch$lifecycle_runtime_release invoke_pc=0x28 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Landroidx/lifecycle/ReportFragment$LifecycleCallbacks;.onActivityPostCreated invoke_pc=0x9 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalArgumentException; escaped the app boundary at Lorg/ecos/logic/flip_a_coin/MainActivity;.onCreate invoke_pc=0x5c depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `evidence/s25/flip_w1e/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](evidence/s25/flip_w1e/screenshot.png)

### Output Frame

- **File:** `evidence/s25/flip_w1e/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](evidence/s25/flip_w1e/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261122-055104-6147`
- **Generated:** 2026-11-22 05:51:06 UTC
