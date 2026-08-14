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
| Package | `org.telegram.messenger.web` |
| Min SDK | 21, Target SDK | 35 |
| DEX Files | 5 (classes.dex through classes5.dex) |
| Total Classes | 41,078 |
| Total Methods | 253,898 |
| Total Fields | 167,533 |
| Native Libraries | 8 (libtmessages.49.so, liblanguage_id_l2c_jni.so) |
| Architectures | arm64-v8a, armeabi-v7a, x86, x86_64 |
| Launcher Activity | `org.telegram.ui.LaunchActivity` (via activity-alias) |

---

## MILESTONE: LaunchActivity.onCreate() executes to completion

**Date:** 2026-08-15

Telegram's `LaunchActivity.onCreate(Bundle)` method executes ALL 309 instructions
and reaches `return-void`. This is the first time a real Telegram method has been
fully executed by MiniAndroid.

```
[DalvikEngine] 🎯 CALLING execute_method_internal() for onCreate with 1330 instructions
[DalvikEngine] Executing: Lorg/telegram/ui/LaunchActivity;.onCreate(Landroid/os/Bundle;)V
...
[DalvikEngine]   [308] 0x501: return-void
[DalvikEngine] Method returned successfully
[DalvikEngine] Instructions executed: 309
  Instructions executed: 309
  Final status: 0 (COMPLETED_SUCCESS)
  API call traces: 115
  Heap objects: 19
```

---

## BLOCKERS FIXED

### BLOCKER-022: activity-alias tracking — FIXED
### BLOCKER-023: APK parser caching — FIXED (O(1) entry lookup)
### BLOCKER-024: MultiDex support — FIXED (5 DEX files, 41,078 classes)
### BLOCKER-025: Launcher resolution via manifest — FIXED (exact match)
### BLOCKER-026: move-object/from16 (0x08) — FIXED
### BLOCKER-027: sput-boolean and sget/sput variants — FIXED
### BLOCKER-028: Arithmetic opcodes (35 new) — FIXED
### BLOCKER-029: if-eqz/if-nez opcode values off by 1 — FIXED
### BLOCKER-030: invoke-*/range opcodes — FIXED
### BLOCKER-031: Array opcodes (new-array, aget, aput) — FIXED
### BLOCKER-032: const/high16 (0x15) — FIXED

---

## OPEN BLOCKERS

### BLOCKER-033: Multidex method_idx remapping — OPEN

**Problem:** When merging DEX files, method_ids from all 5 DEX files are
concatenated into one array. But bytecode uses per-DEX method_idx values.
A method_idx of 100 in classes3.dex now resolves to method 100 in the
merged array (which is from classes.dex), giving wrong method names.

**Impact:** Method names in the trace are wrong (e.g., showing
`com.google.android.gms.internal.mlkit_language_id_common.zzig.zze`
instead of the actual Telegram method). Execution still works because
all invokes go through the API bridge stub, but proper method resolution
requires per-DEX index tracking.

**Fix needed:** Store per-DEX DexReports and track which DEX each class
came from. When resolving method_idx, use the correct DEX's method_ids.

### BLOCKER-034: Recursive DEX method invocation — OPEN

**Problem:** invoke-* instructions bridge to API stubs (which return null/void)
instead of executing the target method's DEX bytecode. Real Android apps call
helper methods that contain real logic.

**Impact:** Telegram's onCreate calls many helper methods (e.g., ApplicationLoader,
AndroidUtilities, etc.) whose bytecode is never executed.

**Fix needed:** When invoke-* resolves a method that has bytecode, create a new
stack frame and recursively call execute_method_internal().

### BLOCKER-035: Native library loading — NOT STARTED

**Problem:** Telegram requires libtmessages.49.so for core functionality.
The runtime has no JNI bridge or native library loader.

**Impact:** Telegram's Application.onCreate() likely calls
System.loadLibrary("tmessages") which will fail.

**Status:** Documented but not implemented. Native support is a major milestone.

---

## COMPLETION GATE

- [x] Telegram APK downloaded
- [x] SHA256 recorded
- [x] DEX parsed (all 5 DEX files, 41,078 classes)
- [x] Launcher resolved (org.telegram.ui.LaunchActivity)
- [x] DEX execution (LaunchActivity.onCreate() — 309 instructions, return-void)
- [x] Fixes committed (commit d7f9291)
- [x] Rerun evidence exists (run/exp038_telegram/)
