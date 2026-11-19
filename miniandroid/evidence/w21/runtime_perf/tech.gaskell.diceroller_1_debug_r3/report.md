# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/upload/handoff_apks/tech.gaskell.diceroller_1_debug.apk`
- **Package:** `tech.gaskell.diceroller`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 31 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 2 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 2751 |
| `TraceEngine` | 3 |
| `Unknown` | 2 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 2657 |
| `ExecutionEngine.stage_render_frame` | 62 |
| `ExecutionEngine.stage_capture_output` | 6 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_initialize_runtime` | 3 |
| `Unknown.Unknown` | 2 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Ltech/gaskell/diceroller/MainActivity;.createWelcomeDialog invoke_pc=0xb depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Ltech/gaskell/diceroller/MainActivity;.onCreate invoke_pc=0x9 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `evidence/w21/runtime_perf/tech.gaskell.diceroller_1_debug_r3/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 22.47 KB

![Screenshot](evidence/w21/runtime_perf/tech.gaskell.diceroller_1_debug_r3/screenshot.png)

### Output Frame

- **File:** `evidence/w21/runtime_perf/tech.gaskell.diceroller_1_debug_r3/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 12.78 KB

![Screenshot](evidence/w21/runtime_perf/tech.gaskell.diceroller_1_debug_r3/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261119-141548-5794`
- **Generated:** 2026-11-19 14:15:54 UTC
