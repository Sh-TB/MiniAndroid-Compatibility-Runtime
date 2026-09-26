# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/s107_apks/it.fast4x.riplay.apk`
- **Package:** `it.fast4x.riplay`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 24 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 14602 |
| `TraceEngine` | 3 |
| `Unknown` | 24 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 14566 |
| `Unknown.Unknown` | 24 |
| `ExecutionEngine.stage_capture_output` | 6 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/data/Database$Companion;.<init> invoke_pc=0x5 depth=17
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/data/Database$Companion;.<clinit> invoke_pc=0x2 depth=16
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/data/Database;.<clinit> invoke_pc=0x0 depth=15
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/extensions/appsettings/AppSettingsManager;.<init> invoke_pc=0x5 depth=14
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainApplication;.appSettingsManager_delegate$lambda$0 invoke_pc=0x2 depth=13
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainApplication;.$r8$lambda$lTyLLUbx5_NcOnmyp5tSLDLS-V4 invoke_pc=0x0 depth=12
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainApplication$$ExternalSyntheticLambda1;.invoke invoke_pc=0xa depth=11
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainApplication;.getAppSettingsManager invoke_pc=0x2 depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainApplication$onCreate$2;.invokeSuspend invoke_pc=0x20 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lkotlinx/coroutines/BuildersKt;.runBlockingK$default invoke_pc=0x2 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainApplication;.onCreate invoke_pc=0x28 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lit/fast4x/riplay/MainActivity;.onCreate invoke_pc=0x19 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainApplication;.appSettingsManager_delegate$lambda$0 invoke_pc=0x2 depth=12
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainApplication;.$r8$lambda$lTyLLUbx5_NcOnmyp5tSLDLS-V4 invoke_pc=0x0 depth=11
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainApplication$$ExternalSyntheticLambda1;.invoke invoke_pc=0xa depth=10
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainApplication;.getAppSettingsManager invoke_pc=0x2 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainActivity;.appSettingsManager_delegate$lambda$0 invoke_pc=0x9 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainActivity;.$r8$lambda$RrZI3CvioNLLT88o5yMeiwNSHmU invoke_pc=0x0 depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainActivity$$ExternalSyntheticLambda42;.invoke invoke_pc=0x10 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainActivity;.getAppSettingsManager invoke_pc=0x2 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lit/fast4x/riplay/MainActivity;.enableFullscreenMode invoke_pc=0x3e depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lit/fast4x/riplay/MainActivity;.onCreate invoke_pc=0x103 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lit/fast4x/riplay/MainActivity;.onCreate invoke_pc=0x117 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/it.fast4x.riplay_run1/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/it.fast4x.riplay_run1/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/it.fast4x.riplay_run1/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/it.fast4x.riplay_run1/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260926-180846-1358`
- **Generated:** 2026-09-26 18:08:48 UTC
