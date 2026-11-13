# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/evidence/s151_trains/store_fr.neamar.kiss_224/data/data/app/fr.neamar.kiss/base.apk`
- **Package:** `fr.neamar.kiss`
- **Status:** **SUCCESS** ✅

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 2 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 14 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 1241 |
| `TraceEngine` | 3 |
| `Unknown` | 14 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 1191 |
| `ExecutionEngine.stage_render_frame` | 18 |
| `Unknown.Unknown` | 14 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lfr/neamar/kiss/DataHandler;.getTagsHandler invoke_pc=0x8 depth=11
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lfr/neamar/kiss/preference/TagsSelectPreference;.setEntries$4 invoke_pc=0xa depth=10
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lfr/neamar/kiss/preference/TagsSelectPreference;.<init> invoke_pc=0x3 depth=9
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/preference/PreferenceInflater;.rInflate invoke_pc=0x6d depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/preference/PreferenceInflater;.rInflate invoke_pc=0x77 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/preference/PreferenceManager;.setDefaultValues invoke_pc=0x1e depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lfr/neamar/kiss/MainActivity;.onCreate invoke_pc=0xa depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lfr/neamar/kiss/forwarder/OreoShortcuts;.applyTheme invoke_pc=0x4c depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lfr/neamar/kiss/forwarder/ForwarderManager;.<init> invoke_pc=0x13 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/IllegalArgumentException; escaped the app boundary at Lfr/neamar/kiss/MainActivity;.onCreate invoke_pc=0x19 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/AppCompatEditText;.<init> invoke_pc=0x21 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lfr/neamar/kiss/ui/SearchEditText;.<init> invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lfr/neamar/kiss/MainActivity;.onCreate invoke_pc=0x69 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lfr/neamar/kiss/MainActivity;.onCreate invoke_pc=0xe4 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `/home/z/my-project/evidence/s151_trains/run_fr.neamar.kiss_224/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 7.91 MB

![Screenshot](/home/z/my-project/evidence/s151_trains/run_fr.neamar.kiss_224/screenshot.png)
- **SHA256:** `6b3bbf6d2f3bc5db3e281a98442e1f761bdcb6b372bde4823483b2d3a8c8b836` (recorded by tools/report_sanity_fix.py from the actual retained file)

## Session Info

- **Session ID:** `EXP-001-20261102-161713-7648`
- **Generated:** 2026-11-02 16:17:14 UTC
