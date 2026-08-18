# MiniAndroid Agent State

## Current Experiment
EXP-060 — Autonomous Intro-to-Login Campaign

## Current Commit
727574b — EXP-060: Generic event dispatch → LoginActivity PROVEN

## Status: LOGIN UI PROVEN ✅

The runtime dispatches a synthetic CLICK on IntroActivity's startMessagingButton
through Telegram's REAL callback chain, creating a LoginActivity object and
triggering its full Fragment lifecycle including createView (1167 code units).

## Root Causes Fixed (EXP-060)
1. ViewShadow::handles_class — broadened for user-defined View subclasses
2. try_shadow_dispatch — uses args[0].class_desc (runtime class) for ctx
3. if-eq/if-ne 22t — fixed mixed NULL_REF/OBJECT_REF comparison (null==nonnull=FALSE)
4. fill-array-data (opcode 0x25) — implemented (was throwing Larray; exceptions)
5. Overload resolution — now matches parameter TYPES, not just count

## Metrics (EXP-060 final)
- Unique methods: 891 (was 558)
- Instructions: 46,843
- HALT: 2 (AndroidUtilities.replaceTags — not a blocker)
- LoginActivity methods: 111 (was 3)
- LoginActivity.onFragmentCreate: REACHED ✅
- LoginActivity.createView (1167 code units): REACHED ✅
- LoginActivity.onResume: REACHED ✅
- PhoneView created (1292 code units): YES ✅
- AnimatedPhoneNumberEditText: YES ✅
- CustomPhoneKeyboardView with NumberButtonView: YES ✅

## Checkpoints (all PROVEN)
A. LaunchActivity entered ✅
B. LaunchActivity completed ✅
C. IntroActivity created ✅
D. IntroActivity view created ✅
E. Interactive View created ✅ (startMessagingButton)
F. Listener attached ✅ (setOnClickListener stored)
G. Synthetic click delivered ✅ (dispatch_click)
H. Real Telegram callback executed ✅ (Lambda2.onClick)
I. Real navigation code executed ✅ (presentFragment)
J. LoginActivity created by app code ✅ (new LoginActivity())
K. LoginActivity lifecycle entered ✅ (onFragmentCreate)
L. LoginActivity createView executed ✅ (1167 code units)
M. Login View hierarchy created ✅ (PhoneView, EditText, KeyboardView)
N. Real Login input/control exists ✅ (AnimatedPhoneNumberEditText, NumberButtonView)
O. Login UI logical state proven ✅

## Regression Tests
- 6 EXP-052 tests PASS
- 4 EXP-059 opcode tests PASS
- Total: 10/10 PASS

## Key Files
- src/dex/dalvik_engine.h — dispatch_click, dispatch_click_by_class, FILL_ARRAY_DATA
- src/dex/dalvik_engine.cpp — if-eq 22t fix, fill-array-data impl, overload type matching
- src/framework/android_shadows.h — ViewNode listener fields, find_all_with_click_listener
- src/framework/android_shadows.cpp — setOnClickListener handler, handles_class broadened
- src/runtime/application_runtime.cpp — synthetic CLICK campaign after execute_apk_with_activity
- docs/EXP060_BASELINE.md, docs/EXP060_REPORT.md

## Resume Instructions
1. Build: `cd miniandroid && bash build_exp042.sh`
2. Run: `./build_exp042/miniandroid_exp042 download/exp038_telegram/Telegram.apk run/exp060_overload`
3. Read this file + worklog.md + docs/EXP060_REPORT.md for context
4. Check run/exp060_overload/ for evidence

## Next Blockers (if continuing)
1. AndroidUtilities.replaceTags HALT-LOOP (text formatting)
2. R-class <clinit> for Landroidx/* (resource IDs still 0)
3. Typed catch handlers (currently only catch-all)
4. Cross-APK validation (currently only Telegram + EXP-052 corpus)
