# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s207/runs/store_s232_opensudoku/data/app/org.moire.opensudoku/base.apk`
- **Package:** `org.moire.opensudoku`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 11 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 4 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 1869 |
| `TraceEngine` | 3 |
| `Unknown` | 4 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 1803 |
| `ExecutionEngine.stage_render_frame` | 33 |
| `ExecutionEngine.stage_capture_output` | 6 |
| `ExecutionEngine.trace_files` | 5 |
| `Unknown.Unknown` | 4 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_initialize_runtime` | 3 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_load_apk` | 2 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `TraceEngine.start_session` | 1 |
| `ExecutionEngine.validation` | 1 |
| `ExecutionEngine.stage_frame_sequence` | 1 |
| `ExecutionEngine.stage_execute_application` | 1 |
| `ExecutionEngine.phase_b_click` | 1 |
| `ExecutionEngine.lifecycle_verified` | 1 |
| `ExecutionEngine.lifecycle_source` | 1 |

## Errors & Issues

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Ltf;.onCreate invoke_pc=0x40 depth=19
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lbe0;.<init> invoke_pc=0x28 depth=18
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lbe0;.<init> invoke_pc=0x28 depth=18
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lxf;.l invoke_pc=0x1d depth=17
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s232/runs/s232_opensudoku/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 308.66 KB

![Screenshot](/home/z/my-project/evidence/s232/runs/s232_opensudoku/screenshot.png)
- **SHA256:** `a7071553237e80a972e6ba32b2101e82e877e429e437ce3791bb4f91acd80ab9` (recorded by tools/report_sanity_fix.py from the actual retained file)

## Session Info

- **Session ID:** `EXP-001-20261113-213315-5601`
- **Generated:** 2026-11-13 21:33:18 UTC
