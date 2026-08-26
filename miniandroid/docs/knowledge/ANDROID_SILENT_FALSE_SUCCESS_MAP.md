# Android Silent False-Success Map

**Last Updated:** 2026-08-26
**Primary Branch HEAD:** `d030657`

This document tracks known silent false-success behaviors in the MiniAndroid
runtime. Silent false-success is when a missing API or capability returns
a value that appears successful but is actually wrong/empty/default.

## Known Silent False-Success Behaviors

### 1. Thread.getStackTrace() → empty array
- **Status:** PARTIAL — returns empty array (length=0)
- **Impact:** Apps that iterate stack trace elements may infinite-loop
  if they don't check array length before accessing elements.
- **Affected apps:** dooz (io.github.yamin8000.dooz) — TIMEOUT
- **Root cause:** No real stack trace capture. Returns empty array.
- **Fix priority:** MEDIUM — requires real stack trace infrastructure.

### 2. getSystemService() → null
- **Status:** HONEST — returns null, not fake success
- **Impact:** Apps that expect non-null service objects get NPE.
- **Affected apps:** Telegram, openlauncher
- **Root cause:** No real system service implementation.
- **Fix priority:** HIGH (F007) — affects many apps.

### 3. StackTraceElement.getClassName() → empty string
- **Status:** SILENT FALSE-SUCCESS — returns empty string
- **Impact:** Code comparing class names never matches → infinite loops.
- **Affected apps:** dooz
- **Root cause:** No real stack trace data.
- **Fix priority:** MEDIUM — related to #1.

### 4. checkSelfPermission() → not implemented
- **Status:** OPEN — no permission model (F008)
- **Impact:** Permission checks may default to granted or fail silently.
- **Affected apps:** Any app requesting permissions.
- **Fix priority:** HIGH (F008) — security-sensitive.

### 5. Resources.getBoolean/getInteger/getStringArray → stubbed
- **Status:** PARTIAL — getString works (resource_values.json), others stubbed
- **Impact:** Apps using getBoolean/getInteger/getStringArray get defaults.
- **Fix priority:** MEDIUM.

### 6. MotionEvent → not implemented
- **Status:** OPEN — no touch event infrastructure
- **Impact:** Apps using touch events get no events.
- **Fix priority:** HIGH for games and interactive apps.

### 7. Handler.postDelayed delay → ignored (treated as 0)
- **Status:** PARTIAL — delay is read but treated as 0 in deterministic mode
- **Impact:** Apps relying on timing delays don't get real delays.
- **Fix priority:** LOW — deterministic mode is intentional.

## False-Success Audit Results (Corpus)

| App | Silent False-Success | Impact |
|-----|---------------------|--------|
| uNote | None detected | PASS |
| microtimer | None detected | PASS |
| simplekeyboard | None detected | PASS |
| bgclock | None detected | PASS |
| stopwatch | Possible — exit=1 but renders UI | PARTIAL |
| dooz | getStackTrace + StackTraceElement | TIMEOUT |
| openlauncher | Manifest parse failure → UnknownApp | FAIL |
| tictactoe | None detected (no rendering) | PASS |

---

## OpenLauncher Investigation Update (2026-08-26)

### Root Cause: CORRUPT APK FILE (not MiniAndroid bug)
- APK file `com.benny.openlauncher_39.apk` has NO End of Central Directory record
- Python's `zipfile.ZipFile()` also fails with "File is not a zip file"
- The file starts with valid PK signature but is truncated/corrupted
- This is a DOWNLOAD CORRUPTION issue, not a MiniAndroid compatibility bug
- **Status:** CORRUPT_FILE — not actionable. Need to re-download a fresh APK.

### dooz Timeout Update
- dooz timeout is caused by `Thread.getStackTrace()` returning empty array
- App code iterates array without checking length
- `StackTraceElement.getClassName()` returns empty string
- `String.equals()` never matches → infinite loop
- **Status:** INVESTIGATED — root cause documented. Fix requires real
  stack trace capture infrastructure. Assigned to general Android backlog.
