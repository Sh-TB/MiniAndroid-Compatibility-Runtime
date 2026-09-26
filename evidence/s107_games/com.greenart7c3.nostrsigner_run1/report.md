# MiniAndroid Execution Report

## Application

- **APK:** `/tmp/s107_apks/com.greenart7c3.nostrsigner.apk`
- **Package:** `com.greenart7c3.nostrsigner`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 17 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 9145 |
| `TraceEngine` | 3 |
| `Unknown` | 17 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 9111 |
| `Unknown.Unknown` | 17 |
| `ExecutionEngine.stage_capture_output` | 6 |
| `ExecutionEngine.trace_files` | 5 |
| `ExecutionEngine.stage_render_frame` | 4 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/vitorpamplona/quartz/utils/urldetector/detection/UrlDetector;.<init> invoke_pc=0x8 depth=11
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/vitorpamplona/quartz/utils/Rfc3986;.parse invoke_pc=0x5 depth=10
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/vitorpamplona/quartz/utils/Rfc3986;.normalize invoke_pc=0x3 depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/vitorpamplona/quartz/nip01Core/relay/normalizer/RelayUrlNormalizer$Companion;.norm invoke_pc=0x4 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lcom/vitorpamplona/quartz/nip01Core/relay/normalizer/RelayUrlNormalizer$Companion;.normalize invoke_pc=0x10 depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lcom/greenart7c3/nostrsigner/models/AmberSettingsKt;.<clinit> invoke_pc=0x4 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lcom/greenart7c3/nostrsigner/models/AmberSettingsKt;.getDefaultAppRelays invoke_pc=0x0 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lcom/greenart7c3/nostrsigner/models/AmberSettings;.<init> invoke_pc=0x6 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lcom/greenart7c3/nostrsigner/Amber;.<init> invoke_pc=0x65 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalArgumentException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at <unknown>.<unknown> invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/internal/MainDispatchersKt;.createMissingDispatcher invoke_pc=0x3 depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/internal/MainDispatchersKt;.createMissingDispatcher$default invoke_pc=0xb depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/internal/MainDispatchersKt;.createMissingDispatcher$default invoke_pc=0xb depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/internal/MainDispatcherLoader;.loadMainDispatcher invoke_pc=0x5e depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/internal/MainDispatcherLoader;.<clinit> invoke_pc=0xd depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalStateException; unwound Lkotlinx/coroutines/Dispatchers;.getMain invoke_pc=0x0 depth=5
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/com.greenart7c3.nostrsigner_run1/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/com.greenart7c3.nostrsigner_run1/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s107_games/com.greenart7c3.nostrsigner_run1/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s107_games/com.greenart7c3.nostrsigner_run1/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20260926-175925-2177`
- **Generated:** 2026-09-26 17:59:27 UTC
