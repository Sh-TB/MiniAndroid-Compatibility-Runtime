# Coder 3 Knowledge Archive

**Mission:** Android System Compatibility Laboratory.

**Status:** Active (system lab, no GitHub write access)

## System Contract Findings

### F002 HIGH: openFileOutput path divergence
- `openFileOutput("../escape.txt", 0)` diverged from Android path semantics.
- **IMPORTANT:** NO ACTUAL SANDBOX ESCAPE was observed.
- Keep SECURITY ESCAPE separate from COMPATIBILITY DIVERGENCE.

### F003 MEDIUM: getDatabasePath path mangling
- `getDatabasePath("../escape.db")` silently mangled/sanitized path semantics.

### F004 HIGH: SystemClock absent/zero
- `uptimeMillis`, `elapsedRealtime`, `elapsedRealtimeNanos` were absent/zero.
- This is related to the C2-F12 wide-value findings (return-wide was missing).

### F005 CRITICAL: Application lifecycle not real DEX
- `Application.attach` / `Application.onCreate` were not actually invoked as real DEX lifecycle code.
- The runtime merely recorded lifecycle text in the observed implementation.
- Potentially blocks app-scoped initialization.

### F006 HIGH: No stable Application singleton
- `Activity.getApplication()` could return null.
- Related to F005.

### F007 HIGH: getSystemService hardcoded null
- `getSystemService(name)` observed hardcoded to return null.

### F008 HIGH: Permission model absent
- Permission model absent/catch-all could silently return GRANTED.

### F009 HIGH: Intent/ActivityResult stubbed
- IntentShadow recorded information but did not perform full launch semantics.

### F010 HIGH: Service/BroadcastReceiver/ContentProvider absent
- These Android components are absent or stubbed.

### F011 HIGH: PackageManager.getPackageInfo hardcoded
- Hardcoded Telegram-specific: packageName = "org.telegram.messenger.web", versionCode = 9999, versionName = "9.9.9"

## Systemic Finding

**Pattern:** unknown method → STUBBED + VOID → later move-result / move-result-wide → silent zero

This can create false success. Unknown API behavior must not silently impersonate successful implementation.

## Methodology

Source grep = discovery only. Important findings require:
1. minimal real APK
2. runtime evidence
3. independent validation
4. regression
5. real APK evidence where applicable

## Contract Statuses

- PROVEN
- PROVEN_PENDING_INDEPENDENT_CHECK
- DIVERGENT
- BLOCKED
- UNSAFE
- UNTESTED

## Useful Artifacts

- docs/system/PRIMARY_CODER_TRANSFER_REPORT.md
- .agent/system-lab-state.md
- .agent/system-lab-worklog.md
- docs/system/ANDROID_API_CONTRACTS.json

---

## Coder 3 Findings Reconciliation (2026-08-26, Primary Coder)

### F002 (openFileOutput path divergence) — PROVEN, KEEP
- File sandbox security is working correctly.
- Do NOT weaken it.

### F003 (getDatabasePath path mangling) — UNTESTED
- Not investigated on current HEAD.

### F004 (SystemClock absent/zero) — RELATED TO C2-F12
- SystemClock methods return 0 because wide-value return was broken.
- C2-F12 (RETURN_WIDE, MOVE_WIDE, MOVE_RESULT_WIDE) is FIXED on main.
- SystemClock should now work if it uses wide returns.
- Status: PARTIALLY RESOLVED (wide values fixed, but SystemClock not explicitly tested)

### F005 (Application lifecycle not real DEX) — OPEN
- ApplicationLoader is pre-populated, not lifecycle-driven.
- No manifest `android:name` extraction → no custom Application instantiation.
- Status: OPEN, high-value generic fix.

### F006 (No stable Application singleton) — RELATED TO F005
- Status: OPEN (same as F005)

### F007 (getSystemService hardcoded null) — PARTIAL
- getSystemService returns null (dalvik_engine.cpp:9482).
- This is HONEST (not fake success) but incomplete.
- Status: PARTIAL — null is better than fake success, but real services are missing.

### F008 (Permission model absent) — OPEN
- No checkSelfPermission/checkPermission implementation exists.
- Status: OPEN — permissions not modeled.

### F009 (Intent/ActivityResult stubbed) — PARTIAL
- IntentShadow records information but does not perform full launch semantics.
- Status: PARTIAL.

### F010 (Service/BroadcastReceiver/ContentProvider absent) — OPEN
- These Android components are absent.
- Status: OPEN.

### F011 (PackageManager hardcoding) — NOT REPRODUCIBLE on current HEAD
- No hardcoded "org.telegram.messenger.web", "9999", "9.9.9" found in runtime code.
- Only in comments/examples in android_context.h.
- Status: NOT REPRODUCIBLE — may have been fixed in a previous commit.

### F012 (catch-all false-success architecture) — NOT INTEGRATED
- F012-AMPLIFIER (commit ab48fbc) is NOT in current main branch history.
- It was from a Coder 3 branch that was never merged.
- Status: OPEN — the catch-all false-success pattern may still exist.
- DO NOT blindly reimplement — investigate current behavior first.

### F013 (move-result-wide destroys INT64) — ALREADY FIXED (C2-F12)
- RETURN_WIDE, MOVE_WIDE, MOVE_RESULT_WIDE all implemented.
- Status: ALREADY FIXED on main.

### F014 (INT64 zero truthiness) — ALREADY FIXED (CM-008)
- if-eqz/if-nez now handle BOOLEAN, BYTE, SHORT, CHAR with int_val==0.
- INT64 zero is handled by the existing INT64 check.
- Status: ALREADY FIXED on main (commit 063c772).

### F015 (runtime-type-only bridge routing) — OPEN
- Related to F012. The bridge may route based on runtime type only.
- F012-AMPLIFIER is not on main.
- Status: OPEN — investigate when relevant.

### F016 (proto resolution falls back to ()V) — IMPLEMENTED
- `resolve_method_proto_for_dex` exists and is called at lines 6993, 7163.
- Status: IMPLEMENTED on main.

### F017 (Makefile header dependencies) — OPEN
- No `-MMD -MP` in Makefile.
- Stale header risk exists.
- Status: OPEN — high-value engineering fix.

### N9 (header dependency tracking) — NOT INTEGRATED
- Not found in current Makefile.
- Status: OPEN — same as F017.

### Multi-DEX run pipeline — WORKING
- `cmd_run` path extracts ALL DEX files (classes.dex through classes5.dex).
- `inject_secondary_dex_classes()` injects all classes.
- Verified: 28557 secondary DEX classes injected (Telegram).
- Status: WORKING on main.
