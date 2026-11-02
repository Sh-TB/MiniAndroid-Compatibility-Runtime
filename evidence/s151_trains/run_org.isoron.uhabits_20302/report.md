# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s151_trains/store_org.isoron.uhabits_20302/data/data/app/org.isoron.uhabits/base.apk`
- **Package:** `org.isoron.uhabits`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 14 |
| Warnings | 1 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 6192 |
| `TraceEngine` | 3 |
| `Unknown` | 14 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 6154 |
| `Unknown.Unknown` | 14 |
| `ExecutionEngine.stage_capture_output` | 9 |
| `ExecutionEngine.trace_files` | 5 |
| `ExecutionEngine.stage_render_frame` | 4 |
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
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |
| `ExecutionEngine.execution_source` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/isoron/uhabits/core/database/UnsupportedDatabaseVersionException; unwound Lorg/isoron/uhabits/HabitsDatabaseOpener;.onCreate invoke_pc=0x10 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/isoron/uhabits/core/database/UnsupportedDatabaseVersionException; unwound Lorg/isoron/uhabits/utils/DatabaseUtils;.openDatabase invoke_pc=0x7 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/isoron/uhabits/core/database/UnsupportedDatabaseVersionException; unwound Lorg/isoron/uhabits/inject/HabitsModule;.<init> invoke_pc=0xc depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lorg/isoron/uhabits/core/database/UnsupportedDatabaseVersionException; unwound Lorg/isoron/uhabits/HabitsApplication;.onCreate invoke_pc=0x86 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Lorg/isoron/uhabits/core/database/UnsupportedDatabaseVersionException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlin/jvm/internal/Intrinsics;.throwUninitializedPropertyAccessException invoke_pc=0x16 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lorg/isoron/uhabits/HabitsApplication$Companion;.getComponent invoke_pc=0x7 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lorg/isoron/uhabits/HabitsApplication;.getComponent invoke_pc=0x2 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lorg/isoron/uhabits/activities/habits/list/ListHabitsActivity;.onCreate invoke_pc=0xe depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlin/jvm/internal/Intrinsics;.throwUninitializedPropertyAccessException invoke_pc=0x16 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lorg/isoron/uhabits/activities/habits/list/ListHabitsActivity;.getAppComponent invoke_pc=0x7 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lorg/isoron/uhabits/activities/habits/list/ListHabitsActivity;.onCreate invoke_pc=0x22 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lorg/isoron/uhabits/inject/DaggerHabitsActivityComponent$Builder;.habitsApplicationComponent invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lorg/isoron/uhabits/activities/habits/list/ListHabitsActivity;.onCreate invoke_pc=0x26 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s151_trains/run_org.isoron.uhabits_20302/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s151_trains/run_org.isoron.uhabits_20302/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s151_trains/run_org.isoron.uhabits_20302/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s151_trains/run_org.isoron.uhabits_20302/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261102-161953-5740`
- **Generated:** 2026-11-02 16:19:54 UTC
