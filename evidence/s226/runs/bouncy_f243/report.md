# MiniAndroid Execution Report

## Application

- **APK:** `upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk`
- **Package:** `com.dozingcatsoftware.bouncy`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 34 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 6 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 1587 |
| `TraceEngine` | 3 |
| `Unknown` | 6 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 1348 |
| `ExecutionEngine.stage_render_frame` | 137 |
| `ExecutionEngine.blit_gl_surface_at` | 34 |
| `ExecutionEngine.stage_gl_surfaces` | 34 |
| `Unknown.Unknown` | 6 |
| `ExecutionEngine.stage_capture_output` | 6 |
| `ExecutionEngine.trace_files` | 5 |
| `ExecutionEngine.stage_initialize_runtime` | 3 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.create_view_from_dalvik_result` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |
| `TraceEngine.start_session` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.create_hello_world_view` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/dozingcatsoftware/vectorpinball/model/FieldLayout;.createFieldElements invoke_pc=0x46 depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/dozingcatsoftware/vectorpinball/model/FieldLayout;.<init> invoke_pc=0xce depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/dozingcatsoftware/vectorpinball/model/Field;.resetForLayoutMap invoke_pc=0xb depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/dozingcatsoftware/vectorpinball/model/Field;.resetForLayoutMap invoke_pc=0x5 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/dozingcatsoftware/bouncy/BouncyActivity;.resetFieldForCurrentLevel invoke_pc=0x8 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lcom/dozingcatsoftware/bouncy/BouncyActivity;.onCreate invoke_pc=0x69 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `evidence/s226/runs/bouncy_f243/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 6.31 KB

![Screenshot](evidence/s226/runs/bouncy_f243/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261112-174357-9516`
- **Generated:** 2026-11-12 17:44:06 UTC
