# EXP-038 — Telegram Reality Validation Blockers

**Started:** 2026-08-15
**Last Updated:** 2026-08-15
**Target:** Real Telegram Android APK (82.7MB, official from telegram.org)

---

## Telegram APK Metadata

| Field | Value |
|-------|-------|
| APK Path | `download/exp038_telegram/Telegram.apk` |
| Size | 82,680,854 bytes (78.9 MB) |
| SHA256 | `193ad551e2cbb745387f26370369f9cd0cf0353ecbc318398ada087ac2bf945e` |
| SHA1 | `e85eb1668c450fccc64fd87c2b98f8eb43949e16` |
| Package | `org.telegram.messenger.web` |
| Min SDK | 21 |
| Target SDK | 35 |
| DEX Files | 5 (classes.dex through classes5.dex) |
| Total Classes | 41,078 |
| Total Methods | 253,898 |
| Total Fields | 167,533 |
| Total Strings | 259,552 |
| Native Libraries | 8 (4 architectures × 2 libs) |
| Native Libs | `libtmessages.49.so`, `liblanguage_id_l2c_jni.so` |
| Architectures | arm64-v8a, armeabi-v7a, x86, x86_64 |
| ZIP Entries | 11,531 |
| Launcher Activity | `org.telegram.ui.LaunchActivity` (via activity-alias) |

---

## BLOCKER-022: Manifest reader didn't track activity-alias — FIXED

### Evidence
```
[ManifestReader] Activity: org.telegram.ui.LaunchActivity
[ManifestReader] Found MAIN action
[ManifestReader] Activity: org.telegram.ui.BubbleActivity
...
(no "Found LAUNCHER category" anywhere)
Main Activity: (empty)
Launcher resolved: androidx.activity.ComponentActivity$1
```

### Root Cause
Telegram uses `<activity-alias>` elements (not `<activity>`) to declare
launcher intent-filters. The manifest reader only set `in_activity_=true`
for `name=="activity"`, not for `name=="activity-alias"`. All LAUNCHER
categories were inside activity-alias elements and were skipped.

### Fix
- `process_start_element`: also track `activity-alias` elements
- `process_end_element`: also check `activity-alias` for END_ELEMENT
- Capture `targetActivity` attribute and use it as the real main activity
- Only set `main_activity` on FIRST match (Telegram has 6+ launcher aliases)

### Verification
After fix:
```
[ManifestReader] Found LAUNCHER category
[ManifestReader] Main Activity: org.telegram.ui.LaunchActivity
```

---

## BLOCKER-023: APK parser crashes on 82MB Telegram APK — OPEN

### Evidence
```
$ ./build/miniandroid_megabatch download/exp038_telegram/Telegram.apk run/exp038_telegram/
[Phase A] Loading APK: download/exp038_telegram/Telegram.apk
Segmentation fault (core dumped)
```

ASan trace:
```
ERROR: AddressSanitizer: SEGV on unknown address 0x0000000001a6
SUMMARY: AddressSanitizer: SEGV src/apk/apk_parser.cpp:264
```

### Root Cause
The APK parser loads the entire 82MB APK into memory and parses all
11,531 ZIP central directory entries. The crash occurs at line 264
of `apk_parser.cpp` during `parse_apk_data`. Likely a stack overflow
or memory allocation issue when handling the large ZIP structure.

### Fix
Not yet implemented. Needs investigation of APK parser memory handling
for large APKs. Possible approaches:
1. Use memory-mapped I/O instead of loading entire APK into memory
2. Optimize ZIP central directory parsing to avoid excessive allocations
3. Add proper bounds checking for large entry counts

### Status: OPEN

---

## BLOCKER-024: Multidex — only classes.dex loaded — OPEN

### Evidence
```
[State] MANIFEST_RESOLVED → DEX_LOADED: DEX loaded: 12521 classes
  Classes: 12521
  Methods: 65452
```

Telegram has 5 DEX files with 41,078 total classes. Only `classes.dex`
(12,521 classes) is loaded. The other 4 DEX files (classes2.dex through
classes5.dex) are not parsed.

### Root Cause
`ApplicationRuntime::load_dex()` only extracts and parses `classes.dex`
from the APK. It does not handle multidex APKs.

### Fix
Not yet implemented. Need to:
1. Extract all `classes*.dex` files from the APK
2. Parse each one
3. Merge the DexReports (or use a combined DexReport)

### Status: OPEN

---

## COMPLETION GATE

- [x] Telegram APK downloaded
- [x] SHA256 recorded (193ad551e2cbb745387f26370369f9cd0cf0353ecbc318398ada087ac2bf945e)
- [ ] DEX parsed (PARTIAL — only classes.dex, BLOCKER-024)
- [x] Launcher resolved (org.telegram.ui.LaunchActivity via activity-alias)
- [x] First crash/blocker documented (BLOCKER-023)
- [x] Fixes committed
- [ ] Rerun evidence exists (blocked by BLOCKER-023)
