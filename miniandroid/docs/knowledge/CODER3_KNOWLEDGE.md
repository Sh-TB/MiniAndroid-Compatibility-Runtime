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
