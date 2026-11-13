# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s186_s107/reruns/store_bouncy/data/app/com.dozingcatsoftware.bouncy/base.apk`
- **Package:** `com.dozingcatsoftware.bouncy`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 6 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 13 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 1406 |
| `TraceEngine` | 3 |
| `Unknown` | 13 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 1348 |
| `ExecutionEngine.stage_render_frame` | 25 |
| `Unknown.Unknown` | 13 |
| `ExecutionEngine.stage_capture_output` | 6 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_initialize_runtime` | 2 |
| `ExecutionEngine.stage_frame_sequence` | 1 |
| `TraceEngine.start_session` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |

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

- **File:** `/home/z/my-project/evidence/s186_s107/reruns/bouncy/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s186_s107/reruns/bouncy/screenshot.png)
- **SHA256:** `dd0c14257fa1f2af1f3478e87fdcf90ffef9682c0287f6ac272fb136d2b9e871` (recorded by tools/report_sanity_fix.py from the actual retained file)

## Session Info

- **Session ID:** `EXP-001-20261106-144630-2807`
- Run id: `EXP-001-20261106-144630-2807` (derived from the report\'s own Session ID line)
- **Generated:** 2026-11-06 14:46:32 UTC
