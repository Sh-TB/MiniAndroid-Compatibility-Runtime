# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/s107_apks/nodomain.playmaker.apk`
- **Package:** `nodomain.playmaker`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 2 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 3939 |
| `TraceEngine` | 3 |
| `Unknown` | 2 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 3905 |
| `ExecutionEngine.stage_capture_output` | 6 |
| `ExecutionEngine.trace_files` | 5 |
| `ExecutionEngine.stage_render_frame` | 4 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
| `Unknown.Unknown` | 2 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |
| `ExecutionEngine.execution_source` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.create_view_from_dalvik_result` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/RuntimeException; unwound Lorg/godotengine/godot/GodotActivity;.onCreate invoke_pc=0x3a depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/RuntimeException; escaped the app boundary at Lcom/godot/game/GodotApp;.onCreate invoke_pc=0x6 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/nodomain.playmaker_run1/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/nodomain.playmaker_run1/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/nodomain.playmaker_run1/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/nodomain.playmaker_run1/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260926-161503-4943`
- **Generated:** 2026-09-26 16:15:04 UTC
