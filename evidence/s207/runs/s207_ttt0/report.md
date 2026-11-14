# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s207/runs/store_s207_ttt0/data/app/com.emmanuelmess.tictactoe/base.apk`
- **Package:** `com.emmanuelmess.tictactoe`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 41 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 2 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 2335 |
| `TraceEngine` | 3 |
| `Unknown` | 2 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 2138 |
| `ExecutionEngine.stage_render_frame` | 82 |
| `ExecutionEngine.blit_gl_surface_at` | 41 |
| `ExecutionEngine.stage_gl_surfaces` | 41 |
| `ExecutionEngine.stage_capture_output` | 6 |
| `ExecutionEngine.trace_files` | 5 |
| `ExecutionEngine.stage_initialize_runtime` | 3 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `TraceEngine.log_screenshot` | 2 |
| `Unknown.Unknown` | 2 |
| `ExecutionEngine.validation` | 1 |
| `TraceEngine.start_session` | 1 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `ExecutionEngine.stage_frame_sequence` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/GdxRuntimeException; unwound Lcom/badlogic/gdx/backends/android/AndroidApplication;.<clinit> invoke_pc=0x0 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Lcom/badlogic/gdx/utils/GdxRuntimeException; unwound Lcom/emmanuelmess/tictactoe/AndroidLauncher;.<init> invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s207/runs/s207_ttt0/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 3.21 MB

![Screenshot](/home/z/my-project/evidence/s207/runs/s207_ttt0/screenshot.png)

### Output Frame

- **File:** `/home/z/my-project/evidence/s207/runs/s207_ttt0/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 3.21 MB

![Screenshot](/home/z/my-project/evidence/s207/runs/s207_ttt0/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261114-125156-9569`
- **Generated:** 2026-11-14 12:52:08 UTC
