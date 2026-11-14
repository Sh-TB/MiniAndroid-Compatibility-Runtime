# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s207/runs/store_s207_gold_bouncy/data/app/com.dozingcatsoftware.bouncy/base.apk`
- **Package:** `com.dozingcatsoftware.bouncy`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 9 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 13 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 1437 |
| `TraceEngine` | 3 |
| `Unknown` | 13 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 1348 |
| `ExecutionEngine.stage_render_frame` | 37 |
| `Unknown.Unknown` | 13 |
| `ExecutionEngine.blit_gl_surface_at` | 9 |
| `ExecutionEngine.stage_gl_surfaces` | 9 |
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
| `ExecutionEngine.execution_source` | 1 |
| `TraceEngine.start_session` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |
| `ExecutionEngine.create_hello_world_view` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/SharedLibraryLoadRuntimeException; unwound Lcom/badlogic/gdx/physics/box2d/Box2D;.init invoke_pc=0x7 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/SharedLibraryLoadRuntimeException; unwound Lcom/dozingcatsoftware/bouncy/BouncyActivity;.<clinit> invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Lcom/badlogic/gdx/utils/SharedLibraryLoadRuntimeException; escaped the app boundary at Lcom/dozingcatsoftware/bouncy/BouncyActivity;.onCreate invoke_pc=0x36 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NoClassDefFoundError; escaped the app boundary at Lcom/dozingcatsoftware/bouncy/BouncyActivity;.onCreate invoke_pc=0x63 depth=1 [APP-BOUNDARY]
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

- **Message:** [EXC-UNWIND] Ljava/lang/NoClassDefFoundError; unwound Lcom/dozingcatsoftware/bouncy/BouncyActivity;.highScoresFromPreferences invoke_pc=0x8 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NoClassDefFoundError; unwound Lcom/dozingcatsoftware/bouncy/BouncyActivity;.highScoresFromPreferencesForCurrentLevel invoke_pc=0x2 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NoClassDefFoundError; escaped the app boundary at Lcom/dozingcatsoftware/bouncy/BouncyActivity;.onCreate invoke_pc=0xbd depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NoClassDefFoundError; unwound Lcom/dozingcatsoftware/bouncy/BouncyActivity;.lastScoreFromPreferences invoke_pc=0x8 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NoClassDefFoundError; unwound Lcom/dozingcatsoftware/bouncy/BouncyActivity;.lastScoreFromPreferencesForCurrentLevel invoke_pc=0x2 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NoClassDefFoundError; escaped the app boundary at Lcom/dozingcatsoftware/bouncy/BouncyActivity;.onCreate invoke_pc=0xc3 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s207/runs/s207_gold_bouncy/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 33.43 KB

![Screenshot](/home/z/my-project/evidence/s207/runs/s207_gold_bouncy/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s207/runs/s207_gold_bouncy/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 33.43 KB

![Screenshot](/home/z/my-project/evidence/s207/runs/s207_gold_bouncy/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261114-124631-7200`
- **Generated:** 2026-11-14 12:46:55 UTC
