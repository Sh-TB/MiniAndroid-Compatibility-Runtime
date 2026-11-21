# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/apk_cache/com.itsfrz.tictactoe_5.apk`
- **Package:** `com.itsfrz.tictactoe`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 31 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 9 |
| Warnings | 1 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 4522 |
| `TraceEngine` | 3 |
| `Unknown` | 9 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 4425 |
| `ExecutionEngine.stage_render_frame` | 62 |
| `Unknown.Unknown` | 9 |
| `ExecutionEngine.stage_capture_output` | 7 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_initialize_runtime` | 3 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
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

- **Message:** [EXC-UNWIND] LC4/a; unwound LC4/u;.s invoke_pc=0x8d depth=20
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] LC4/a; unwound LB3/a;.e invoke_pc=0x4f depth=18
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] LC4/a; unwound LB4/c;.e invoke_pc=0xd8 depth=17
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] LC4/a; unwound LN1/r;.q invoke_pc=0x50 depth=15
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] LC4/a; unwound LN1/r;.g invoke_pc=0xc depth=14
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound LU1/r;.<init> invoke_pc=0x45 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/navigation/fragment/NavHostFragment;.<init> invoke_pc=0x0 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Li/D;.k invoke_pc=0x17 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lcom/itsfrz/tictactoe/MainActivity;.onCreate invoke_pc=0xcd depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `evidence/s21/ws1b_itsfrz_r3/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](evidence/s21/ws1b_itsfrz_r3/screenshot.png)

### Output Frame

- **File:** `evidence/s21/ws1b_itsfrz_r3/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](evidence/s21/ws1b_itsfrz_r3/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261121-173652-4564`
- **Generated:** 2026-11-21 17:37:05 UTC
