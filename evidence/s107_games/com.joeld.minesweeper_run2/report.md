# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/s107_apks/com.joeld.minesweeper.apk`
- **Package:** `com.joeld.minesweeper`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 3 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 6448 |
| `TraceEngine` | 3 |
| `Unknown` | 3 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 6410 |
| `ExecutionEngine.stage_render_frame` | 6 |
| `ExecutionEngine.stage_capture_output` | 6 |
| `ExecutionEngine.trace_files` | 5 |
| `Unknown.Unknown` | 3 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/RuntimeException; unwound Lkotlin/jvm/internal/Intrinsics;.checkNotNull invoke_pc=0x2 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/RuntimeException; unwound Lcom/joeld/minesweeper/HomeActivity;.setupInsets invoke_pc=0x21 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/RuntimeException; escaped the app boundary at Lcom/joeld/minesweeper/HomeActivity;.onCreate invoke_pc=0x48 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/com.joeld.minesweeper_run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/com.joeld.minesweeper_run2/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/com.joeld.minesweeper_run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/com.joeld.minesweeper_run2/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260926-163934-3337`
- **Generated:** 2026-09-26 16:39:35 UTC
