# MiniAndroid Agent State

## Current Experiment
EXP-059 — Fragment Forensics, Generic Initialization, and Autonomous Login-UI Progression

## Current Commit
6f5a030 — EXP-059: Add opcode regression tests + remove loadCurrentState stub

## Status: INTRO UI PROVEN ✅ / LOGIN UI NOT PROVEN

The runtime now executes a complete Fragment lifecycle on IntroActivity,
including `createView` (608 code units, real subclass implementation),
`onResume`, and `onBecomeFullyVisible`. Real View objects are created
(ViewPager, RLottieImageView, BottomPagesView, IntroAdapter).

LoginActivity is NOT reached because `getClientNotActivatedFragment`
correctly returns IntroActivity on first launch (empty SharedPreferences
→ `currentViewNum == 0` → if-eqz branches to IntroActivity path). This
is correct first-launch behavior, not a bug.

## Root Cause Fixed (EXP-059)
The runtime's Opcode enum was systematically OFF BY ONE compared to
AOSP source code. This affected:
- if-* opcodes (0x37-0x3c → 0x38-0x3d)
- 2addr opcodes (0xb1-0xcf → 0xb0-0xce)
- INT binops (0x91-0x9b → 0x90-0x9a)
- conversion opcodes (0x82-0x90 → 0x81-0x8f)
- FLOAT/DOUBLE binops (0xa7-0xb0 → 0xa6-0xaf)
- cmp-* opcodes (0x2c-0x30 → 0x2d-0x31)

The most damaging effect: byte 0x38 (intended: if-eqz) was dispatched to
execute_if_nez, INVERTING the branch direction. This caused
addFragmentToStack to return false at PC=26 instead of continuing to
setParentLayout at PC=27.

The EXP-058 "if-ltz INT32 hack" was a workaround for this same bug —
when byte 0x39 (intended: if-nez) was dispatched to execute_if_ltz,
the hack made if-ltz behave like if-nez for INT32 values. With the
opcode table fixed, the hack is removed.

## Baseline Metrics (EXP-059 final)
- Unique methods: 558 (was 454)
- HALT: 0
- Instructions: 50,221 (was 38,879)
- setParentLayout calls: 4 (was 0)
- createView calls (real subclass): 3 (was 0)
- IntroActivity.createView (608 code units): executes end-to-end
- View-like classes instantiated: 65

## Fragment Lifecycle Progress (PROVEN)
- getClientNotActivatedFragment → returns IntroActivity ✅
- addFragmentToStack → returns TRUE ✅
- IntroActivity.onFragmentCreate ✅
- BaseFragment.setParentLayout (polymorphic dispatch to IntroActivity) ✅
- ActionBarLayout.attachView ✅
- IntroActivity.createView (real subclass method!) ✅
- IntroActivity.attachSheets ✅
- IntroActivity.onResume ✅
- IntroActivity.onBecomeFullyVisible ✅
- ViewPager, RLottieImageView, BottomPagesView created ✅

## Key Fixes Applied (EXP-059)
1. AOSP opcode table fix (if-*, 2addr, binop, cmp-*) — ROOT CAUSE
2. invoke-virtual polymorphism: dispatch using runtime_type first
3. Removed EXP-058 if-ltz INT32 hack (no longer needed)
4. Removed EXP-058 loadCurrentState stub (now executes correctly)
5. Added Util.toByteArray stub (InputStream.read returns 0 not -1)
6. Added [FRAGMENT-LIFECYCLE] event log
7. Added 4 new regression tests (exp059_opcode_regression.py) that
   DISTINGUISH if-eqz from if-nez (old tests passed by coincidence)

## Regression Tests
- 6 EXP-052 tests PASS (with updated OP_IF_EQZ=0x38, OP_IF_NEZ=0x39)
- 4 EXP-059 tests PASS (verify actual branch direction via instruction count)
- Total: 10/10 PASS

## Checkpoints
- CHECKPOINT_I_INTRO_UI = PROVEN
- CHECKPOINT_L_LOGIN_UI = NOT_PROVEN
  (LoginActivity not reached because bytecode correctly returns
  IntroActivity on first launch — would need to seed SharedPreferences
  or simulate intro completion, both are application-specific)

## Key Files
- src/dex/dalvik_engine.h — Opcode enum fixed
- src/dex/dalvik_engine.cpp — removed if-ltz hack, polymorphism fix, FRAGMENT-LIFECYCLE log
- docs/EXP059_BASELINE.md — Phase 0 baseline
- docs/EXP059_REPORT.md — final report
- tools/exp059_disasm.py — AOSP-standard disassembler
- tools/exp059_andro_disasm.py — androguard cross-check
- tools/exp059_opcode_regression.py — 4 new distinguishing tests
- tools/exp059_dump_view_tree.py — extracts View hierarchy from runtime log
- run/exp059_lifecycle/login_view_tree.json — View hierarchy summary

## Resume Instructions
1. Build: `cd miniandroid && bash build_exp042.sh`
2. Run: `./build_exp042/miniandroid_exp042 download/exp038_telegram/Telegram.apk run/exp059_lifecycle`
3. Read this file + worklog.md + docs/EXP059_REPORT.md for context
4. Check run/exp059_lifecycle/ for evidence

## Next Blockers (if continuing toward Login)
1. R-class <clinit> for Landroidx/* — would require resources.arsc parsing
2. Typed catch handlers (currently only catch-all)
3. Exception propagation across method boundaries
4. Cross-APK validation (currently only Telegram + EXP-052 corpus)
5. To reach LoginActivity specifically: would need to either seed
   SharedPreferences with currentViewNum > 0 (state hack) or simulate
   IntroActivity's "Start Messaging" button click (UI event simulation)
