# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/upload/handoff_apks/io.github.herrerad85.tallybook_94.apk`
- **Package:** `io.github.herrerad85.tallybook`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 31 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 23 |
| Warnings | 1 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `DalvikEngine` | 3 |
| `ExecutionEngine` | 6951 |
| `TraceEngine` | 3 |
| `Unknown` | 23 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_classes` | 6856 |
| `ExecutionEngine.stage_render_frame` | 62 |
| `Unknown.Unknown` | 23 |
| `ExecutionEngine.stage_capture_output` | 7 |
| `ExecutionEngine.trace_files` | 5 |
| `DalvikEngine.execute_apk` | 3 |
| `ExecutionEngine.stage_initialize_runtime` | 3 |
| `TraceEngine.log_screenshot` | 2 |
| `ExecutionEngine.trace_export` | 2 |
| `ExecutionEngine.stage_execute_application_real_dalvik` | 2 |
| `ExecutionEngine.stage_parse_dex` | 2 |
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

- **Message:** [EXC-UNWIND] Ljava/lang/IllegalArgumentException; unwound Lcom/oriondev/moneywallet/App;.onCreate invoke_pc=0x1a depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/oriondev/moneywallet/ui/activity/base/ThemedActivity;.onCreate invoke_pc=0x3e depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lcom/oriondev/moneywallet/ui/activity/LauncherActivity;.onCreate invoke_pc=0x0 depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/emoji2/viewsintegration/EmojiTextViewHelper;.setEnabled invoke_pc=0x2 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/AppCompatEmojiTextHelper;.setEnabled invoke_pc=0x2 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/AppCompatEmojiTextHelper;.loadFromAttributes invoke_pc=0x1f depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/AppCompatTextView;.<init> invoke_pc=0x32 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/AppCompatTextView;.<init> invoke_pc=0x3 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/oriondev/moneywallet/ui/view/theme/ThemedTextView;.<init> invoke_pc=0x0 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/oriondev/moneywallet/ui/activity/base/ThemedActivity;.setContentView invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/emoji2/viewsintegration/EmojiTextViewHelper;.setEnabled invoke_pc=0x2 depth=8
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/AppCompatEmojiTextHelper;.setEnabled invoke_pc=0x2 depth=7
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/AppCompatEmojiTextHelper;.loadFromAttributes invoke_pc=0x1f depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/AppCompatTextView;.<init> invoke_pc=0x32 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/appcompat/widget/AppCompatTextView;.<init> invoke_pc=0x3 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/oriondev/moneywallet/ui/view/theme/ThemedTextView;.<init> invoke_pc=0x0 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/oriondev/moneywallet/ui/activity/base/ThemedActivity;.setContentView invoke_pc=0x0 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/oriondev/moneywallet/ui/activity/LauncherActivity;.getColorBehindStatusBar invoke_pc=0x0 depth=6
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/oriondev/moneywallet/ui/activity/base/ThemedActivity;.onThemeSystemBarIcons invoke_pc=0x10 depth=5
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/oriondev/moneywallet/ui/activity/base/ThemedActivity;.setupActivityBaseTheme invoke_pc=0x3 depth=4
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/oriondev/moneywallet/ui/activity/base/ThemedActivity;.onThemeSetup invoke_pc=0x0 depth=3
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Lcom/oriondev/moneywallet/ui/activity/base/ThemedActivity;.onPostCreate invoke_pc=0x7 depth=2
- **Location:** `.`
- **Fatal:** No

### EXC-UNCAUGHT-TOP

- **Message:** [EXC-UNCAUGHT-TOP] Ljava/lang/NullPointerException; escaped the app boundary at Lcom/oriondev/moneywallet/ui/activity/LauncherActivity;.onCreate invoke_pc=0x9b depth=1 [APP-BOUNDARY]
- **Location:** `.`
- **Fatal:** No

## Screenshots

### Output Frame

- **File:** `evidence/w21/runtime_perf/io.github.herrerad85.tallybook_94_r3/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](evidence/w21/runtime_perf/io.github.herrerad85.tallybook_94_r3/screenshot.png)

### Output Frame

- **File:** `evidence/w21/runtime_perf/io.github.herrerad85.tallybook_94_r3/screenshot.png`
- **Resolution:** 1080x1920
- **Size:** 10.11 KB

![Screenshot](evidence/w21/runtime_perf/io.github.herrerad85.tallybook_94_r3/screenshot.png)

## Session Info

- **Session ID:** `EXP-001-20261119-141304-3781`
- **Generated:** 2026-11-19 14:13:16 UTC
