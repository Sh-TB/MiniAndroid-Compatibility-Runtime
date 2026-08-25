# Coder-Main (Primary) Knowledge Archive

**Coder**: Super Z (Primary Coder — owns main branch, has GitHub push access)
**Last Updated**: 2026-08-26
**Primary Branch HEAD**: `bd7ae8d`

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
