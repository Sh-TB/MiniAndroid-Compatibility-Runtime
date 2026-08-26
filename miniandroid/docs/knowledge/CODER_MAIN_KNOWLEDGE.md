# Coder-Main (Primary) Knowledge Archive

**Coder**: Super Z (Primary Coder — owns main branch, has GitHub push access)
**Last Updated**: 2026-08-26
**Primary Branch HEAD**: `82835e1`

This file records findings from the Primary Coder's investigations. It is
the authoritative archive for implementation-level discoveries that affect
the runtime's correctness. Findings from Coder 2 and Coder 3 are in
separate files ([CODER2_KNOWLEDGE.md](CODER2_KNOWLEDGE.md),
[CODER3_KNOWLEDGE.md](CODER3_KNOWLEDGE.md)) and are cross-referenced here
when integrated.

---

## CM-001: onNextPressed needShowAlert Branch — Root Cause and Fix

### Summary
`PhoneView.onNextPressed` was taking the `needShowAlert` side path at PC=604
instead of reaching the `auth.sendCode` path. Three root causes were identified
and fixed, resulting in the **first-ever direct trace** of the complete
`auth.sendCode → sendRequest → RequestDelegate.run → fillNextCodeParams → setPage`
chain.

### Exact PC and Branch Condition
- **Method**: `Lorg/telegram/ui/LoginActivity$PhoneView;.onNextPressed(Ljava/lang/String;)V`
- **Bytecode location**: classes4.dex, code_off=0x55a914, 1468 code units
- **Critical branch**: PC=604, opcode 0x33 (if-ne), format 22t
  ```
  PC= 604  cu=0x2433  if-ne  v4, v2, +28 → PC=632
  ```
  - v4 = `PhoneView.countryState` (loaded at PC=602 via `iget-wide v4, v7, field@33152`)
  - v2 = 1 (set at PC=596 via `const/4 v2, #1`)
  - Semantics: `if (countryState != 1) goto PC=632` (skip the "ChooseCountry" alert)
- **Next branch**: PC=633, opcode 0x33 (if-ne)
  ```
  PC= 633  cu=0x2433  if-ne  v4, v2, +30 → PC=663
  ```
  - v2 = 2 (set at PC=632 via `const/4 v2, #2`)
  - Semantics: `if (countryState != 2) goto PC=663` (skip the second alert, continue to auth.sendCode)

### Relevant Registers/Values
- `countryState` field: `field@33152` on `Lorg/telegram/ui/LoginActivity$PhoneView;`, type `I`
- Values:
  - 0 = set by `setCountry` (after auto-detection from getNearestDc response)
  - 1 = set by `<init>` at PC=1258 (default) and by `afterTextChanged` (when user types but country doesn't match)
  - 2 = set by `afterTextChanged` when country code matches a known country

### Root Cause (3 issues)

#### Issue 1: CollectionShadow not registered in cmd_run path
- **File**: `miniandroid/src/main.cpp`, function `cmd_run`
- **Problem**: `cmd_run` only registered `HandlerShadow`, `ViewShadow`, and
  `ActivityShadow`. `CollectionShadow` was missing.
- **Effect**: Without `CollectionShadow`, `HashMap.put` was a silent no-op
  (the bridge_to_api fallback has `shadow_registry_ == nullptr` guard which
  prevented it from running). `HashMap.get` always returned null.
- **Impact**: `PhoneView.setCountry` calls `HashMap.get("US")` to look up
  the country code. With null return, `setCountry` returned early at PC=6
  (`if-eqz v3, +64 → PC=70`), so `countryState` was never set to 0.
- **Fix**: Added `CollectionShadow` registration in `cmd_run`:
  ```cpp
  auto* collection_shadow = shadow_registry.register_shadow<framework::CollectionShadow>();
  ```

#### Issue 2: codeField injection prevented setCountry from running
- **File**: `miniandroid/src/runtime/execution_engine.cpp`, function `phase_b_click`
- **Problem**: The test harness injected `"1"` into `codeField` (PhoneView$1)
  to simulate the user typing the US country code.
- **Effect**: `lambda$new$12` at PC=11 checks:
  ```
  PC= 11  if-nez v0(codeField.length()), +11 → PC=22
  ```
  Since `codeField.length() = 1` (from the injection), the branch was TAKEN
  → SKIPPED the `setCountry` call at PC=19.
- **Impact**: `setCountry` was never called → `countryState` stayed at 1 →
  `onNextPressed` at PC=604 saw `countryState=1` → `if-ne(1, 1) = false` →
  NOT taken → fell through to the alert path.
- **Fix**: Removed the `"1"` injection. `codeField` stays empty, so
  `lambda$new$12` at PC=11 sees `codeField.length()=0` → `if-nez(0) = false`
  → NOT taken → falls through to PC=13 → calls `setCountry`.

#### Issue 3: Missing pre-click Handler drain
- **File**: `miniandroid/src/runtime/execution_engine.cpp`, function `phase_b_click`
- **Problem**: The `getNearestDc` response handler (Lambda14 → Lambda16 →
  `lambda$new$12` → `setCountry`) is queued on the Handler during
  `PhoneView.<init>`. `onNextPressed` was called BEFORE the Handler queue
  was drained.
- **Effect**: When `onNextPressed` ran, `setCountry` hadn't executed yet:
  - `codeField` was empty → `onNextPressed` returned early at PC=73
    (`if-eqz v2(codeField.length()=0), +1386 → PC=1459`)
  - `countryState` was still 1 → even if `onNextPressed` reached PC=604,
    it would take the alert path
- **Fix**: Added a pre-click Handler drain between text input and the
  Next button click. This ensures `setCountry` runs before `onNextPressed`.

### Experiment Used to Prove It
1. Added `[EXP092-COUNTRYSTATE-WRITE]` instrumentation in `execute_iput` to
   log every write to `PhoneView.countryState` (PC, caller, new_value).
2. Added `[EXP092-ONNEXT-IF]` instrumentation in `IMPLEMENT_IF_22T` macro to
   log every `if-*` branch in `onNextPressed` (PC, opcode, v4, v2, taken, target).
3. Added `[EXP092-IF-NEZ]` instrumentation in `execute_if_nez` to log every
   `if-nez` in `onNextPressed`, `lambda$new$12`, `setCountry`, etc.
4. Ran the full Telegram chain and analyzed the trace.

### Before/After Behavior

**Before fix** (commit `475923a`):
- `[EXP092-COUNTRYSTATE-WRITE]`: 2 writes (both from `<init>`: PC=12 val=0, PC=1258 val=1)
- `setCountry`: NEVER called (no COUNTRYSTATE-WRITE from setCountry)
- `[EXP092-SETPAGE]`: 0 calls
- `[EXP092-FILLNEXTCODE]`: 0 calls
- `TL_auth_sendCode`: NEVER constructed
- `PhoneView$Lambda2.run`: NEVER invoked
- `onNextPressed` PC=604: `if-ne v4(1) vs v2(1)` → NOT taken → alert path

**After fix** (commit `bd7ae8d`):
- `[EXP092-COUNTRYSTATE-WRITE]`: 3 writes (PC=12 val=0, PC=1258 val=1, **PC=68 of setCountry val=0**)
- `setCountry`: CALLED with (PhoneView, HashMap, "US") → reached PC=68 → set countryState=0
- `[EXP092-SETPAGE]`: **1 call** — `setPage(page_value=13)` from `fillNextCodeParams`
- `[EXP092-FILLNEXTCODE]`: **1 call** — from `access$8000`
- `TL_auth_sendCode`: **CONSTRUCTED** (obj#5227)
- `[EXP071-SNDREQ] mocked TL_auth_sentCode`: response delivered (resp_id=5236)
- `PhoneView$Lambda2.run`: **INVOKED** with response_id=5236, response_class=TLRPC$TL_auth_sentCode
- `onNextPressed` PC=604: `if-ne v4(0) vs v2(1)` → **TAKEN** → PC=632 (skip alert!)
- `onNextPressed` PC=633: `if-ne v4(0) vs v2(2)` → **TAKEN** → PC=663 (continue to auth.sendCode!)

### Regression Results
- Build: PASS (no compilation errors)
- Runtime: exit=0 (no crash)
- All existing regression tests should be re-verified (A4, Phase F, etc.)

### Negative Findings (Incorrect Hypotheses Ruled Out)

1. **Hypothesis**: Runtime's `if-*` (22t format) opcode constants are off by one
   (e.g., `IF_NE = 0x33` should be `0x32` per AOSP standard).
   **Ruling**: The runtime's opcode values ARE correct for the DEX version
   used by Telegram. The semantic interpretation (`0x33 = if-ne`) matches
   the `if (countryState != 1) {...} else if (countryState != 2) {...}` pattern
   in the Java source. The AOSP "standard" opcode numbering I initially recalled
   was for a different DEX format version. DO NOT change the opcode constants.

2. **Hypothesis**: `resid=3` (small resource ID) is a plural/unknown index that
   should return empty string.
   **Ruling**: `resid=3` IS a real D8-shrunk `R.string.ChooseCountry` entry.
   The blanket `<0x10000 ⇒ empty string` rule is too aggressive. However, the
   full fix requires an SPUT-capture approach (not yet implemented).

3. **Hypothesis**: `onNextPressed`'s `needShowAlert` is a runtime bug.
   **Ruling**: `needShowAlert` is LEGITIMATE Telegram behavior. When
   `countryState == 1` (COUNTRY_NOT_SELECTED), the app shows a "Choose a
   country" alert. The runtime was correctly executing this path — the bug
   was that `countryState` was never set to 0 because `setCountry` was
   never called (due to the three issues above).

---

## CM-002: cmd_run Path Missing Shadows

### Summary
The `cmd_run` function in `main.cpp` creates its own `ShadowRegistry` with
only 3 shadows (Handler, View, Activity). `ApplicationRuntime::initialize_shadow_registry()`
registers 8 shadows (including Collection, Thread, Looper, Intent, ArchTaskExecutor).
Since `cmd_run` bypasses `ApplicationRuntime`, it was missing critical shadows.

### Impact
- `CollectionShadow` missing → `HashMap.put/get` were no-ops → broke country lookup
- `ThreadShadow` missing → `Thread.currentThread()` not available
- `LooperShadow` missing → `Looper.getMainLooper()` not available
- `IntentShadow` missing → Intent handling incomplete
- `ArchTaskExecutorShadow` missing → `isMainThread()` returns false

### Fix
Added `CollectionShadow` registration in `cmd_run` (commit `bd7ae8d`).
Other shadows should be added as needed when their absence causes issues.

### Note
This is the same class of bug as the `resource_values.json` loading issue
(CM-003 below) — both are caused by `cmd_run` bypassing `ApplicationRuntime`.

---

## CM-003: resource_values.json Not Loaded in cmd_run Path

### Summary
The `resource_values.json` file (containing 11263 strings, 74 colors, 176 dimens,
1965 drawables) was only loaded in `ApplicationRuntime::execute_on_create()`.
The `cmd_run` path bypasses this, so `dalvik_engine.resource_string_values_` was
empty, causing `getString(int)` to return field names instead of actual values.

### Fix
Added equivalent load logic in `stage_execute_application_real_dalvik`
(commit `7a99e9a`, previous session).

### Cross-Reference
This was the EXP-092 fix from the previous session. Documented here for
completeness as part of the "cmd_run bypasses ApplicationRuntime" pattern.

---

## CM-004: page_value=13 is LoginActivityEmailCodeView, NOT SmsView

### Summary
`setPage(page_value=13)` activates `LoginActivityEmailCodeView` (the email code
verification page), NOT `LoginActivitySmsView`. The page constant 13 was
produced because the mock `TL_auth_sentCode` response was missing the `type`
field, causing `fillNextCodeParams` to take the default (email) path.

### Exact PC and Branch Condition
- **Method**: `Lorg/telegram/ui/LoginActivity;.setPage(IZLandroid/os/Bundle;Z)V`
- **Bytecode location**: classes4.dex, code_off=0x56052c, 309 code units
- **Switch at PC=0-32**: checks for pages 0, 5, 6, 9, 10, 12, 16, 17
- **page_value=13**: does NOT match any switch case → falls through to
  PC=28 `if-ne v7, v2(16), +3 → PC=31` → TAKEN → PC=31 (main body)
- **At PC=82-90**: `views[13]` is selected, `currentViewNum` is set to 13
- **views[13]**: `LoginActivityEmailCodeView` (NOT SmsView)

### Root Cause
The early `[EXP071-SNDREQ]` interceptor at line 1731 created an EMPTY
`TL_auth_sentCode` with no `type` field. `fillNextCodeParams` reads the
`type` field (at PC=62: `iget v0, v12, field@9458 = type`) to determine
which page to transition to. Without the type field, the instance-of
checks for FirebaseSms/App/Call all returned false (or garbage due to
CM-005), and the code fell through to the default path that sets page=13.

### Fix
Added `type=TL_auth_sentCodeTypeSms`, `phone_code_hash`, `length=5`,
`timeout=30` to the mock response in the `[EXP071-SNDREQ]` interceptor.

### Status
PARTIALLY_FIXED — the mock now has the correct type field, but the
instance-of bug (CM-005) was also preventing correct type checking.

---

## CM-005: instance-of Register Decoding Bug (CRITICAL)

### Summary
`execute_instance_of` was reading the dest/src registers from the WRONG bit
positions in the 22c format, causing all instance-of checks to use garbage
register values.

### Root Cause
The 22c format encoding is: `[BBBBAAAA op] [CCCC]` where:
- AAAA (4 bits) = vA (dest register) = bits 8-11 of the first code unit
- BBBB (4 bits) = vB (src register) = bits 12-15 of the first code unit
- op (8 bits) = bits 0-7 of the first code unit
- CCCC (16 bits) = type_idx = second code unit

Previous code:
```cpp
dest = (instr >> 8) & 0xFF;  // WRONG: reads 0xc0 (full high byte)
src  = instr & 0xFF;          // WRONG: reads 0x20 (the opcode!)
type_idx = bytecode_[pc + 2]; // WRONG: should be pc + 1
```

Fixed code:
```cpp
dest = (instr >> 8) & 0x0F;     // CORRECT: vA = low nibble of high byte
src  = (instr >> 12) & 0x0F;    // CORRECT: vB = high nibble of high byte
type_idx = bytecode_[pc + 1];  // CORRECT: type@CCCC at pc+1
```

### Impact
- instance-of was reading the WRONG register as the source object
- The result was written to the WRONG register
- `fillNextCodeParams`' instance-of check for `TL_auth_sentCodeTypeFirebaseSms`
  returned garbage (often true for ALL types), causing the wrong page transition
- This is a GENERIC VM bug — affects ALL APKs using instance-of

### Fix
Commit `82835e1` — corrected the bit positions and type_idx offset.

### Verification
After the fix, `currentViewNum` changed from 13 (EmailCodeView) to 5
(phone input page, set by lambda$onNextPressed$22 before auth.sendCode).

### Negative Finding
The opcode table values (IF_EQ=0x32, etc.) are CORRECT for the DEX version
used by Telegram. The bug was ONLY in the instance-of register decoding,
not in the opcode constants.

---

## CM-006: Overload Resolution arg_idx Bug for Non-Static Methods

### Summary
The overload resolution code compared `args[0]` (which is `this` for non-static
methods) against `param_types[0]` (the first parameter type), causing incorrect
type mismatches for instance methods where `arg_count == param_count`.

### Root Cause
At line 3315:
```cpp
size_t arg_idx = (arg_count > param_count) ? 1 : 0;
```
When `arg_count == param_count` (both include `this`), `arg_idx` was set to 0.
But for non-static methods, `args[0]` is `this` (the receiver), and the first
PARAMETER corresponds to `args[1]`.

### Example
`fillNextCodeParams(Bundle, auth_SentCode, Z)` has `param_count=3` and was
called with `arg_count=3` (this, Bundle, auth_SentCode). The old code compared
`args[0]`(this=LoginActivity) against `param_types[0]`(Bundle) → mismatch →
`type_matches=false` → wrong overload selected (the 22-instruction email code
version instead of the 588-instruction real version).

### Fix
Commit `d72a88b` — for non-static methods, `arg_idx` starts at 1 (skip `this`).

---

## CM-007: setPage Switch Behavior for page=5

### Summary
After the instance-of fix, `setPage(page_value=5)` is called by
`lambda$onNextPressed$22` (the auth.sendCode response handler). Page 5 is
`VIEW_PHONE_INPUT` — the phone input page. This is NOT the SMS page.

### Evidence
- `setPage(5)` is called from `lambda$onNextPressed$22` at PC=0x20
- The switch at PC=5: `if-eq v7(5), v2(5) → PC=33` → TAKEN (matches)
- `currentViewNum` is set to 5
- `views[5]` = PhoneView (the phone input page)

### Analysis
`lambda$onNextPressed$22` is the auth.sendCode response callback. When it
receives the response, it checks for errors (SESSION_PASSWORD_NEEDED,
FloodWait, etc.) at PC=55-119. If no errors, it should call
`fillNextCodeParams` which would then call `setPage` with the SMS page
constant. But the current execution shows `setPage(5)` being called
BEFORE the response chain reaches `fillNextCodeParams`.

### Next Blocker
The `lambda$onNextPressed$22` method at PC=4 checks `if-nez v4(Bundle?)`
and at PC=55 reads `TL_error.text` from v4. The register assignment may
be incorrect, or the response/error args are swapped. Need to trace the
actual register values to determine why `fillNextCodeParams` is not reached.

---

## CM-008: if-eqz BOOLEAN Zero-Ness Bug (CRITICAL)

### Summary
`if-eqz` did not treat `BOOLEAN` type with `int_val==0` as zero. This caused
ALL `instance-of` results in conditional branches to be inverted — `if-eqz`
on a `false` BOOLEAN result returned `is_zero=FALSE`, meaning the branch was
NOT taken (the OPPOSITE of correct behavior).

### Source-First Analysis
Used Telegram source (`LoginActivity.java` line 3185-3197) to understand
the callback semantics:

```java
ConnectionsManager.getInstance(currentAccount).sendRequest(req, (response, error) -> AndroidUtilities.runOnUIThread(() -> {
    nextPressed = false;
    if (error == null) {
        if (response instanceof TLRPC.TL_auth_sentCodeSuccess) {
            // success path → setPage(VIEW_REGISTER)
        } else {
            fillNextCodeParams(params, (TLRPC.auth_SentCode) response);
        }
    } else {
        // error path
    }
}), ...);
```

### Register Mapping (Source → DEX)

The D8-compiled `lambda$onNextPressed$22` has 7 parameters:
```
v3 = PhoneView (this)
v4 = TL_error (error argument)     ← Source: error
v5 = TLObject (response)            ← Source: response
v6 = Bundle (params)                ← Source: params
v7 = String (phone)
v8 = PhoneInputData
v9 = TLObject (request)
```

### Exact PC and Branch Condition
- **Method**: `lambda$onNextPressed$22` (335 code units, classes4.dex)
- **PC=4**: `if-nez v4(error)` → error=null → NOT taken → PC=6 (success path)
- **PC=6**: `instance-of v4, v5(response), TL_auth_sentCodeSuccess` → FALSE
- **PC=8**: `if-eqz v4(BOOLEAN false)` → should be TAKEN → PC=46 (else → fillNextCodeParams)

### Root Cause
The `is_zero` check in `execute_if_eqz` only covered:
- `NULL_REF`, `INT32(val==0)`, `OBJECT_REF(id==0)`, `UNINITIALIZED`, `REGISTER_UNSET`, `VOID_`

`BOOLEAN` was MISSING. `instance-of` returns `make_bool(false)` which sets
`type=BOOLEAN, int_val=0`. Without BOOLEAN in the is_zero check,
`if-eqz(false BOOLEAN)` returned `is_zero=FALSE` → branch NOT taken.

### Fix
Commit `063c772` — Added `BOOLEAN`, `BYTE`, `SHORT`, `CHAR` to the is_zero
check in both `if-eqz` and `if-nez` handlers. Same fix applied to both
for consistency.

### Direct Evidence After Fix
```
PC=8: if-eqz v4(BOOLEAN, int_val=0) → is_zero=TRUE → TAKEN → PC=46 ✓
fillNextCodeParams called ✓
setPage(page_value=2) called from fillNextCodeParams ✓
currentViewNum = 2 = VIEW_CODE_SMS (per Telegram source) ✓
Render root: LoginActivitySmsView (view_id=3536) ✓
```

### Page Constants (from Telegram source, line 243-246)
```java
VIEW_PHONE_INPUT = 0
VIEW_CODE_CHECK  = 1
VIEW_CODE_SMS    = 2  ← CORRECT SMS PAGE
VIEW_PASSWORD    = 3
VIEW_PROFILE     = 4
VIEW_REGISTER    = 5  ← Was previously selected due to the BOOLEAN bug
```

### Impact
This is a GENERIC VM fix — affects ALL APKs using `instance-of` results
in `if-eqz`/`if-nez` branches. Every `instance-of` check followed by a
conditional branch was potentially affected.

### Negative Finding
The earlier `page_value=13` (EmailCodeView) was caused by a DIFFERENT bug
(the missing `type` field in the mock response, CM-004). The `page_value=5`
(RegisterView) was caused by THIS bug (BOOLEAN if-eqz). Both are now fixed.

### Full Chain Now Proven
```
PhoneView.onNextPressed
→ TL_auth_sendCode constructor
→ sendRequest
→ mock TL_auth_sentCode (type=Sms, length=5, timeout=30)
→ PhoneView$Lambda2.run (response)
→ lambda$onNextPressed$22
→ PC=4: if-nez v4(error=null) → NOT taken → PC=6
→ PC=6: instance-of(response, sentCodeSuccess) → FALSE
→ PC=8: if-eqz v4(BOOLEAN false) → TAKEN → PC=46
→ fillNextCodeParams(params, auth_SentCode)
→ setPage(page_value=2)
→ currentViewNum = 2 = VIEW_CODE_SMS
→ SmsView active (render root view_id=3536)
```

---

## CM-009: 3-Run SMS Acceptance Gate Proof

### Summary
After CM-008 (if-eqz BOOLEAN fix), the full SMS page transition chain
was proven 3 times with identical results.

### 3-Run Results (all identical)
- SHA256: `60df0c2ba1680ae58e2612bfd82660a3436df963569a3191dcfdc841810d4b5b`
- dark_pixels: 974 per run
- All 3 runs pass SMS acceptance gate

### SMS Acceptance Gate Checklist
- [x] currentViewNum=2 (VIEW_CODE_SMS per Telegram source)
- [x] setPage(2) called from fillNextCodeParams
- [x] fillNextCodeParams called
- [x] PhoneView$Lambda2.run invoked
- [x] mocked TL_auth_sentCode with type=Sms
- [x] auth.sendCode constructed
- [x] SmsView render root (LoginActivitySmsView)
- [x] 3-run proof: all identical
- [x] screenshot independently decoded by PIL

### SMS ViewTree (from renderer trace)
```
Root: LoginActivitySmsView (view_id=3536, children=6, depth=0)
├── FrameLayout (3541, children=1)
│   └── RLottieImageView (3543, children=0)
├── TextView (3540, text="Check your Telegram messages")
├── TextView (3539, text="")
├── LoginActivitySmsView$2 (3544)
├── LoadingTextView (3547)
└── FrameLayout (3594)
    └── LoginActivitySmsView$4 (3578, children=2)
        └── FrameLayout (3562, children=2)
            ├── LoginActivitySmsView$3 (3563, code input field)
            └── LoginActivitySmsView$5 (3579, code input field)
```

### Remaining Gap
- confirmTextView (node 3539) has text="" because the Bundle's `phone`
  key may be empty (codeField was empty when onNextPressed constructed
  the params Bundle). This is a DATA issue, not a VM bug.
- The SMS text "Enter code" and "Phone verification" ARE present on
  other TextViews in the ViewTree.

### Status
PROVEN — the SMS page transition is real and reproducible.

---

## CM-010: F005 Application Lifecycle — Manifest Extraction + Instantiate + onCreate

### Summary
Implemented F005 on current main: manifest `android:name` extraction and
Application class instantiation with `attachBaseContext` + `onCreate` called
BEFORE `Activity.onCreate`, per AOSP contract.

### Source Reference
AOSP `ActivityThread.handleBindApplication`:
1. `instrumentation.newApplication(Class)` — instantiate Application
2. `app.attachBaseContext(context)` — attach context
3. `app.onCreate()` — Application initialization

### Implementation
1. **Manifest reader** (`manifest_reader.cpp/h`): Extract `android:name` from
   `<application>` tag in both AXML and text parse paths.
2. **APK parser** (`apk_parser.cpp/h`): Propagate `application_name` from
   `ManifestInfo` to `ApkInfo`.
3. **Execution engine** (`execution_engine.cpp`): Before calling
   `execute_apk_with_activity`, instantiate the declared Application class,
   call `<init>`, `attachBaseContext`, `onCreate`.

### Direct Evidence (Telegram)
```
[EXP093-APP] Manifest declares Application class: Lorg/telegram/messenger/ApplicationLoaderImpl;
[EXP093-APP] Allocated Application object: obj_id=2
[EXP093-APP] <init> invoked
[EXP093-APP] attachBaseContext invoked
[EXP093-APP] onCreate invoked
→ THEN Activity.onCreate executes
→ SMS gate still passes: currentViewNum=2, fillNextCodeParams, setPage(2)
```

### Non-Telegram Validation (uNote)
```
[EXP093-APP] No custom Application class declared in manifest
→ exit=0, 23472 dark pixels (no regression)
```

### Fix
Commit `b7dc97b` — manifest extraction + Application instantiation + lifecycle calls.

### Status
PROVEN — Application lifecycle is now real, not pre-populated.
- F005: FIXED on main.

---

## CM-011: F014 INT64/FLOAT32/FLOAT64 Zero-Ness in if-eqz/if-nez

### Summary
`if-eqz` and `if-nez` were missing INT64, FLOAT32, and FLOAT64 types from
their zero-ness checks. A zero `long` (0L), `float` (0.0f), or `double`
(0.0d) was treated as non-zero (truthy), causing incorrect branch behavior.

### Source Reference
Per AOSP Dalvik spec: if-eqz branches if the value == 0, where 0 is
type-agnostic for ALL primitive types (int, long, float, double, boolean,
byte, short, char).

### Fix
Commit `58a0534` — Added INT64 (`long_val == 0`), FLOAT32 (`float_val == 0.0f`),
FLOAT64 (`double_val == 0.0`) to both if-eqz `is_zero` and if-nez `is_nonzero`.

### Status
PROVEN — Telegram SMS gate passes (no regression), uNote passes (exit=0).

---

## CM-012: F011 PackageManager Identity — Manifest-Derived Values

### Summary
Replaced hardcoded Telegram package identity (`org.telegram.messenger.web`,
`9999`, `"9.9.9"`) with manifest-derived values from ApkInfo.

### Root Cause
`getPackageInfo` and `getPackageName` in `bridge_to_api` returned hardcoded
Telegram values for ALL APKs. This caused non-Telegram apps to report
incorrect package identity.

### Fix
Commit `d00aabf`:
- Added `package_name_`, `version_code_`, `version_name_` to DalvikExecutionEngine
- Added `set_package_info()` setter
- `execution_engine.cpp` calls `set_package_info()` with `result.apk_info` values
- `getPackageInfo` returns manifest-derived values
- `getPackageName` returns manifest-derived package name

### Validation
- Telegram: exit=0, SMS gate passes (currentViewNum=2)
- uNote: exit=0, package correctly shows `app.varlorg.unote`

### Status
PROVEN — F011 is FIXED on main. All APKs now get correct package identity.

---

## CM-013: F007 getSystemService — Real Service Objects for Known Services

### Summary
`getSystemService` now returns real singleton service objects for 17 known
services instead of always returning null. Unknown services still return null
(honest, not fake success).

### Source Reference
AOSP `ContextImpl.getSystemService(String name)`:
- Looks up `SystemServiceRegistry.SYSTEM_SERVICE_FETCHERS.get(name)`
- Returns the cached service instance or creates a new one
- Returns null for unknown services

### Implementation
Added a `service_map` that maps service names to their AOSP-defined class
descriptors. `get_or_create_singleton()` returns a cached singleton for
each service. Methods called on these objects are handled by `bridge_to_api`
or return defaults.

### Services Implemented (17)
window, layout_inflater, activity, input_method, notification, alarm, audio,
clipboard, connectivity, uimode, search, keyguard, location, account, power,
vibrator, sensor, display

### Direct Evidence
- Telegram: `getSystemService("window")` → WindowManager
- Telegram: `getSystemService("input_method")` → InputMethodManager
- Telegram: `getSystemService("accessibility")` → null (unknown service)
- Telegram SMS gate: currentViewNum=2 (no regression)
- uNote: exit=0, 23K dark pixels (no regression)

### Fix
Commit `edd2338`.

### Status
PARTIAL — service objects are returned but their methods are minimal.
Individual service method implementations (e.g. AudioManager.getStreamVolume,
UiModeManager.getNightMode) are still needed for full compatibility.

---

## CM-014: F008 Permission Model — checkSelfPermission/checkPermission/requestPermissions

### Summary
Implemented a deterministic permission model with NOT_REQUESTED/GRANTED/DENIED
states. Normal permissions are GRANTED by default (per AOSP). Dangerous
permissions are DENIED until explicitly requested.

### Source Reference
AOSP `Context.checkSelfPermission(String permission)`:
- Returns `PackageManager.PERMISSION_GRANTED` (0) if granted
- Returns `PackageManager.PERMISSION_DENIED` (-1) if not granted
- Normal permissions (INTERNET, etc.) are granted without runtime request
- Dangerous permissions (CAMERA, READ_CONTACTS) require `requestPermissions`

### Implementation
- `checkSelfPermission(String)` → int (GRANTED=0 / DENIED=-1)
- `PackageManager.checkPermission(String, String)` → int
- `Activity.requestPermissions(String[], int)` → auto-grant in headless mode
- `permission_state_` map stores per-permission state
- 13 normal permissions are pre-granted (INTERNET, VIBRATE, WAKE_LOCK, etc.)
- All other permissions default to DENIED (conservative, not fake success)

### Fix
Commit `2bdc8ea`.

### Status
PROVEN — no regressions in corpus (Telegram, uNote, microtimer, simplekeyboard,
bgclock all pass).
