# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/run/diff366/stores/store_bouncy/data/app/com.dozingcatsoftware.bouncy/base.apk`
- **Package:** `com.dozingcatsoftware.bouncy`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 9 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 1389 |
| `TraceEngine` | 3 |
| `Unknown` | 9 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 1348 |
| `Unknown.Unknown` | 9 |
| `ExecutionEngine.stage_render_frame` | 9 |
| `ExecutionEngine.stage_capture_output` | 8 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
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

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/SharedLibraryLoadRuntimeException; unwound Lcom/badlogic/gdx/utils/SharedLibraryLoader;.loadFile invoke_pc=0x0 depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/SharedLibraryLoadRuntimeException; unwound Lcom/badlogic/gdx/physics/box2d/Box2D;.init invoke_pc=0x7 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/SharedLibraryLoadRuntimeException; unwound Lcom/dozingcatsoftware/bouncy/BouncyActivity;.<clinit> invoke_pc=0x0 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/SharedLibraryLoadRuntimeException; unwound Lcom/dozingcatsoftware/bouncy/BouncyActivity;.getInitialLevel invoke_pc=0x8 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Lcom/badlogic/gdx/utils/SharedLibraryLoadRuntimeException; escaped the app boundary at Lcom/dozingcatsoftware/bouncy/BouncyActivity;.onCreate invoke_pc=0x63 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/RuntimeException; unwound Lcom/dozingcatsoftware/bouncy/FieldLayoutReader;.layoutMapForLevel invoke_pc=0xe depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/RuntimeException; unwound Lcom/dozingcatsoftware/bouncy/BouncyActivity;.resetFieldForCurrentLevel invoke_pc=0x4 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/RuntimeException; escaped the app boundary at Lcom/dozingcatsoftware/bouncy/BouncyActivity;.onCreate invoke_pc=0x69 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lcom/dozingcatsoftware/bouncy/BouncyActivity;.onCreate invoke_pc=0x94 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/diff366/final/bouncy_com.dozingcatsoftware.bouncy/run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/diff366/final/bouncy_com.dozingcatsoftware.bouncy/run2/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/diff366/final/bouncy_com.dozingcatsoftware.bouncy/run2/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/diff366/final/bouncy_com.dozingcatsoftware.bouncy/run2/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261003-020710-2719`
- **Generated:** 2026-10-03 02:07:11 UTC
