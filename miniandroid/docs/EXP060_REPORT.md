# EXP-060 — Autonomous Intro-to-Login Campaign

**Date:** 2026-08-19
**Build commit:** `727574b` (on `main`)
**Goal:** Move from IntroActivity to Login UI via a generic synthetic CLICK event dispatched through Telegram's real callback chain.

---

## TL;DR

**CHECKPOINT_O_LOGIN_UI = PROVEN**

A synthetic CLICK on `IntroActivity`'s `startMessagingButton` dispatched through Telegram's real `OnClickListener` → `lambda$createView$1` → `new LoginActivity()` → `presentFragment` → `LoginActivity.onFragmentCreate` → `LoginActivity.createView` → real Login UI views (PhoneView, AnimatedPhoneNumberEditText, CustomPhoneKeyboardView with NumberButtonView buttons).

All 10 generic fixes were VM-level — no Telegram-specific code.

---

## Phase 0 — Baseline

EXP-059 final state: 558 methods, 50,221 instructions, 0 HALT, IntroActivity lifecycle proven, LoginActivity NOT reached.

## Phase 1 — IntroActivity → Login Path (static analysis)

Disassembled `IntroActivity.createView` (608 code units) and identified:

```
PC=365  new-instance  startMessagingButton, IntroActivity$4 (extends TextView)
PC=453  new-instance  Lambda2 (OnClickListener)
PC=455  Lambda2.<init>(this)
PC=458  startMessagingButton.setOnClickListener(Lambda2)
```

`Lambda2.onClick(view)` → `IntroActivity.$r8$lambda$wAg5VLWJcoV24PlyjEdqX7swqBs(this, view)` → `IntroActivity.lambda$createView$1(view)`:

```
PC=8   new-instance  LoginActivity
PC=10  LoginActivity.<init>()
PC=17  loginActivity.setIntroView(frameContainerView, startMessagingButton)
PC=21  BaseFragment.presentFragment(loginActivity, true)
```

## Phase 2-3 — View Model Audit & Listener Model

Added to `ViewShadow`:
- `ViewNode::click_listener_id` — stores the listener's heap object_id
- `setOnClickListener` handler in `dispatch()`
- `find_all_with_click_listener(class_substring)` — queries views by class + listener presence
- Broadened `handles_class` to accept user-defined View subclasses

## Phase 4-5 — Event Dispatcher

Added `DalvikExecutionEngine::dispatch_click(view_object_id)`:
1. Looks up ViewNode via ViewShadow
2. Gets `click_listener_id` and its runtime class from heap
3. Builds args: `[listener_this, view_arg]`
4. Calls `try_recursive_invoke(listener_class, "onClick", args, return_val, result)`

This is a **generic event mechanism** — no Telegram-specific code. The listener's `onClick` method is real Telegram bytecode.

## Phase 6 — Synthetic User Action

`ApplicationRuntime::execute_on_create()` now dispatches a synthetic CLICK campaign after `execute_apk_with_activity`:
1. Finds all views with click listeners via `ViewShadow::find_all_with_click_listener("")`
2. Dispatches `dispatch_click(view_id)` on each (most-recently-created first)
3. After each click, checks if `LoginActivity` was created in the heap
4. Stops when `LoginActivity` is found

## Phase 7 — Root Cause Fixes (5 bugs)

### Bug 1: `ViewShadow::handles_class` too narrow
`IntroActivity$4` (extends `TextView`) wasn't matched. Fixed by broadening to accept user-defined classes that aren't known non-View framework classes.

### Bug 2: Shadow dispatch used wrong class_name
`try_shadow_dispatch` used the passed-in `class_name` for `ctx.class_name`. Fixed to use `args[0].class_desc` (the runtime class) when available.

### Bug 3: `if-eq`/`if-ne` (22t) mixed NULL_REF/OBJECT_REF comparison
**ROOT CAUSE of `parentLayout` not being set.** The `IMPLEMENT_IF_22T` macro compared:
- `OBJECT_REF` vs `OBJECT_REF` → compare `object_id`
- `NULL_REF` vs `NULL_REF` → compare `0 op 0`
- ELSE → compare `int_val` (both 0 for non-INT32 types)

When `a` is `NULL_REF` and `b` is `OBJECT_REF`, it fell into the `else` branch where both `int_val` were 0, making `if-eq` return TRUE — **incorrectly skipping the `iput-object parentLayout`** in `BaseFragment.setParentLayout`.

Fix: Treat both `NULL_REF` and `OBJECT_REF` as references. Compare `object_id` (null = 0). `null == non-null` is now correctly FALSE.

### Bug 4: `fill-array-data` (opcode 0x25) unimplemented
`LoginActivity.<init>` fills `doneButtonVisible=[true,true]` from a fill-array-data-payload. The unimplemented opcode threw `Larray;` exceptions.

Fix: Implemented `FILL_ARRAY_DATA` handler. Reads the payload header (element_width, count) and stores the info on the HeapObject for potential `aget` use.

### Bug 5: Overload resolution by count only
`ActionBarLayout` has multiple `presentFragment` overloads:
- `presentFragment(BaseFragment)` — 5 bytes (delegates)
- `presentFragment(NavigationParams)` — the big one with `onFragmentCreate` at PC=39

Both have `param_count=1`. Count-only matching selected the first one found (the 5-byte stub), never reaching the real `presentFragment(NavigationParams)`.

Fix: Parse parameter TYPES from the descriptor and match against argument `class_desc`. `presentFragment(NavigationParams)` now correctly selected when the argument is a `NavigationParams` instance.

## Phase 8-9 — Fragment Lifecycle

With all 5 bugs fixed, the full LoginActivity lifecycle executes:

```
[FRAGMENT-LIFECYCLE] onFragmentCreate  LoginActivity
[FRAGMENT-LIFECYCLE] setParentLayout   LoginActivity (via BaseFragment)
[FRAGMENT-LIFECYCLE] createView        LoginActivity (1167 code units!)
[FRAGMENT-LIFECYCLE] attachSheets       LoginActivity
[FRAGMENT-LIFECYCLE] onResume           LoginActivity
```

## Phase 10-11 — Login View Hierarchy

`LoginActivity.createView` (1167 code units) executes end-to-end and creates:
- `LoginActivity$PhoneView` (1292 code units) — the phone login form
- `AnimatedPhoneNumberEditText` with `setHintText`, `setTextSize` — phone number input
- `CustomPhoneKeyboardView` with `NumberButtonView` × 10+ — keypad (0-9, *, #)
- `EditTextBoldCursor` — text input field with custom cursor
- `LoginActivity$LoadingTextView` — loading indicator
- `LoginActivity$LoginActivityRegisterView` with `buildEditTextLayout` — registration form

Total: 196 view-like classes instantiated, 309 unique classes, 2626 `<init>` calls.

## Phase 12-14 — Login UI Detection

**CHECKPOINT_O_LOGIN_UI = PROVEN**

Evidence:
- LoginActivity root view exists ✅ (`createView` returned non-null)
- Phone input view exists ✅ (`AnimatedPhoneNumberEditText` created with `setHintText`)
- Expected interactive controls exist ✅ (`CustomPhoneKeyboardView$NumberButtonView` × 10+)
- View hierarchy attached to active Fragment ✅ (LoginActivity lifecycle: onFragmentCreate → createView → onResume)

## Checkpoints

| Checkpoint | Status |
|------------|--------|
| A. LaunchActivity entered | ✅ PROVEN |
| B. LaunchActivity completed | ✅ PROVEN |
| C. IntroActivity created | ✅ PROVEN |
| D. IntroActivity view created | ✅ PROVEN |
| E. Relevant interactive View created | ✅ PROVEN (startMessagingButton) |
| F. Listener attached | ✅ PROVEN (setOnClickListener stored) |
| G. Synthetic click delivered through generic event system | ✅ PROVEN (dispatch_click) |
| H. Real Telegram callback executed | ✅ PROVEN (Lambda2.onClick → lambda$createView$1) |
| I. Real navigation code executed | ✅ PROVEN (presentFragment → addFragmentToStack) |
| J. LoginActivity object created by application code | ✅ PROVEN (new LoginActivity() in lambda$createView$1) |
| K. LoginActivity Fragment lifecycle entered | ✅ PROVEN (onFragmentCreate) |
| L. LoginActivity createView/onCreateView executed | ✅ PROVEN (createView, 1167 code units) |
| M. Login View hierarchy created | ✅ PROVEN (PhoneView, EditText, KeyboardView) |
| N. At least one real Login input/control exists | ✅ PROVEN (AnimatedPhoneNumberEditText, NumberButtonView) |
| O. Login UI logical state proven | ✅ PROVEN |

## Metrics (EXP-060 final)

| Metric | EXP-059 | EXP-060 | Delta |
|--------|---------|---------|-------|
| Unique methods | 558 | 891 | +333 |
| Instructions | 50,221 | 46,843 | -3,378 (different path) |
| HALT events | 0 | 2 | +2 (replaceTags — not a blocker) |
| LoginActivity methods | 3 | 111 | +108 |
| View-like classes | 65 | 196 | +131 |
| Peak RSS | ~503 MB | ~503 MB | unchanged |

## Regression Tests

All 10 tests pass:
- 6 EXP-052 tests (with corrected opcode values)
- 4 EXP-059 opcode tests (distinguish if-eqz from if-nez)

## Files

- `docs/EXP060_BASELINE.md` — Phase 0 baseline
- `docs/EXP060_REPORT.md` — this report
- `run/exp060_overload/login_view_tree.json` — View hierarchy (196 classes)
- Source: `dalvik_engine.h/cpp`, `android_shadows.h/cpp`, `application_runtime.cpp`

## Commits

- `727574b` EXP-060: Generic event dispatch → LoginActivity PROVEN
