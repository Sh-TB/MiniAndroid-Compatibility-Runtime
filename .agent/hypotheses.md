# Hypotheses Log — EXP-038

## HYP-001: APK parser hang is due to O(n²) entry lookup
**Status:** CONFIRMED
**Evidence:** `extract_entry_from_memory` calls `list_entries_from_data` which re-parses the entire central directory. For Telegram's 11,531 entries, each extraction is O(n), and we extract multiple entries (manifest, each DEX, etc.).
**Action:** Implement caching (BLOCKER-023 fix).

## HYP-002: Telegram uses activity-alias for launcher
**Status:** CONFIRMED
**Evidence:** Python inspection of AndroidManifest.xml showed LAUNCHER categories are inside activity-alias elements (DefaultIcon, NoxIcon, etc.) with targetActivity=org.telegram.ui.LaunchActivity.
**Action:** Implemented in BLOCKER-022 fix.

## HYP-003: Multidex is needed for class resolution
**Status:** CONFIRMED (not yet tested)
**Evidence:** Telegram APK contains 5 DEX files. Current runtime only loads classes.dex (12,521 of 41,078 classes). Any class in classes2-5.dex will not be found.
**Action:** Implement BLOCKER-024.

## HYP-004: Telegram's LaunchActivity.onCreate will need Application class
**Status:** UNTESTED
**Rationale:** Android apps typically have an Application subclass that's initialized before any Activity. Telegram likely has org.telegram.messenger.ApplicationLoader or similar. The runtime may need to handle Application.onCreate() before LaunchActivity.onCreate().
**Action:** Test after P0 fixes.

## HYP-005: Native library loading will block Telegram early
**Status:** UNTESTED
**Rationale:** Telegram's Application.onCreate() likely calls System.loadLibrary("tmessages") which requires JNI support. This will be a hard blocker for full execution.
**Action:** Document but don't implement JNI yet — focus on getting as far as possible in managed code first.
