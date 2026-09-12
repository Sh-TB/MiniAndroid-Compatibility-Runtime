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

---

## SFS-008: ViewShadow.toString returns literal "View" for ANY object (FIXED in CM-018)

**Class**: Object→toString silent false success
**Severity**: CRITICAL — poisoned every string concatenation in the app
**Status**: FIXED (EXP-094 / CM-018)

### Behavior
ViewShadow::dispatch handled `toString` by returning the literal string
"View" — for ANY receiver, including non-View objects that reached it via
bridge_to_api's view_parents fallback (which tries "Landroid/view/View;"
for EVERY method not handled by another shadow). StringBuilder had no
implementation, so `StringBuilder.toString()` returned "View".

### Blast radius (proven by trace)
- LocaleInfo.getKey() → "View" (should be "unofficial_XX")
- "+" + bundle.getString("phone") → "View" (should be "+15551234567")
- PhoneFormat.format(input) → returned "View" unchanged
- formatString("SentSmsCode") → "...your phone **View*." (garbage in user-visible text)
- ANY Object.toString() routed through the fallback → "View"

### Fix
1. ViewShadow::toString now only handles REGISTERED ViewNodes and returns
   an AOSP-style debug string "class_desc{id}".
2. StringBuilder implemented for real (see CM-018) so it never reaches the
   View fallback.

### Regression guard
The SMS screen text MUST contain the real phone number ("+1 5551234567")
and MUST NOT contain "View" as a substring — verified in the 3-run proof.

---

## SFS-009: PNGDecoder rejects palette PNGs (color_type=3) — FIXED in CM-023

**Class**: Asset loading silent-false-success (asset silently missing)
**Severity**: HIGH — 100% of palette PNGs returned empty (the most
common Android image format)
**Status**: FIXED (EXP-096 / CM-023)

### Behavior
PNGDecoder::decode() explicitly rejected color_type=3 PNGs with the
error "palette PNG (color_type=3) not supported". This means EVERY
palette PNG in an APK (emoji, app icons, drawables) silently produced
no pixels. Real Android always handles color_type=3.

### Fix
See CM-023 — added PLTE/tRNS chunk parsing and palette-index expansion
to RGBA. 94% of Telegram PNGs now decode correctly (3% remain —
bit_depth=4 sub-byte palettes, tracked as future work).

### Regression guard
`scripts/exp096_image_pipeline_test.cpp` runs PNGDecoder against all
PNGs in an APK and reports the pass rate. Pass rate must stay above 90%
for the Telegram APK (the corpus has no bit_depth=4 sub-byte PNGs at
the time of writing).
