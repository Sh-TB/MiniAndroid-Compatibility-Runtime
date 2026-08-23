# MiniAndroid Agent State — EXP-089 Campaign

## Current Experiment
EXP-089 — Continue Telegram Phase M after F5 wide-value fixes

## Current Commit (most recent state)
HEAD — 36c61cc — F5 followup: Add MOVE_WIDE opcode (was MISSING from dispatcher)
**PUSHED and VERIFIED: HEAD == origin/main == 36c61cc9690f899faaf75402413f48323daad965**

## Status: 10 PROVEN, 1 IN PROGRESS (M boundary advanced — click dispatched)

### PROVEN (no change)
- A1 AXML inflation
- A2 measure/layout
- A5 text rendering
- A4 drawable/image loading
- B1 valid PNG output
- B5 entry-point resolution
- B generic input/click
- B2 event deduplication
- C SQLite
- F Handler/Looper
- I multi-DEX audit

### IN PROGRESS (M boundary advanced this round)

Phase M now reaches the CLICK DISPATCH and lambda invocation:

```
LaunchActivity.onCreate (1330 instructions) ✅
→ handleIntent (15606 instructions) ✅
→ UserConfig.isClientActivated (EXECUTES) ✅
→ LoginActivity.loadCurrentState (EXECUTES, 209 instructions) ✅
→ IntroActivity.<init> ✅
→ addFragmentToStack (2 args correct) ✅
→ IntroActivity.onFragmentCreate (EXECUTES, 118 instructions) ✅
→ IntroActivity.createView (EXECUTES, 608 instructions) ✅
  - reads R.drawable.telegram_logo, R.string.Page1Title..Page6Title
  - creates RLottieImageView, ScrollView, FrameLayout
  - registers setOnClickListener on 4 views
→ phase_b_click dispatches click on view_id=2559 (TextView) ✅
  - listener = IntroActivity$$ExternalSyntheticLambda3
  - onClick EXECUTES (bytecode_size=6) ✅
  - invokes lambda$createView$2 via invoke-direct ✅
  - 46588 instructions executed, 2618 heap objects
→ [next: lambda$createView$2 should call presentFragment → LoginActivity]
```

### Root-cause fixes this round

1. **F5 CRITICAL FIX: return-wide opcode (0x10) was MISSING from dispatcher**:
   - Opcode 0x10 (return-wide) was not in the case list
   - Fell through to handle_unimplemented → methods returning long/double didn't return
   - Combined with move-result-wide being hardcoded to make_int(0), ALL wide values were lost
   - FIX: Added `case Opcode::RETURN_WIDE` → `execute_return_wide()`
   - Fixed `move-result-wide` to propagate `last_invoke_return_` (was make_int(0))
   - Added `execute_return_wide()` implementation
   - GENERIC fix — affects ALL APKs using long/double returns

2. **F5 followup: MOVE_WIDE opcode (0x04) was MISSING from dispatcher**:
   - Opcode 0x04 (move-wide) was not in the case list
   - Caused halt at PC=0x35ce in Telegram (blocked lambda$createView$2)
   - FIX: Added `case Opcode::MOVE_WIDE` with 12x format handling
   - Coerces non-wide values to INT64 (matches return-wide coercion)

3. **EXP088-PHASE-B diagnostics added**:
   - Logs ViewShadow found + clickable count
   - Logs each clickable view_id, class, listener_id
   - Logs dispatch_click result
   - Confirms phase_b_click IS running and dispatching clicks

### Verified secondary findings
1. **F1 (lazy-load reserve)**: NOT APPLICABLE — no reserve(43895) in primary. Defense-in-depth added.
2. **F4 (type_list 2-byte entries)**: FIXED in previous round. Confirmed working.
3. **F5 (return-wide/move-result-wide)**: FIXED this round. Two critical bugs:
   - return-wide opcode missing from dispatcher
   - move-result-wide hardcoded to 0
   - move-wide opcode also missing (followup)
4. **F2 (fallback method dispatch)**: PENDING audit
5. **F3 (swallowed exceptions)**: PENDING audit
6. **F6 (uninitialized memory)**: PENDING audit (after F1/F4/F5)

## Resume Instructions (next round)

1. The campaign is NOT complete. M is IN PROGRESS.
2. **Current state**: Click on IntroActivity is dispatched, lambda$createView$2 is invoked,
   but the presentFragment → LoginActivity transition hasn't completed yet.
3. **Next boundary**: The halt_reason is "Unimplemented opcode: 0x0x00df at PC=0x5"
   — this is in a stub method, not the main path. Need to investigate whether
   lambda$createView$2 actually calls presentFragment and whether LoginActivity
   gets created.
4. Reproducer:
   ```
   cd miniandroid && ./build/miniandroid run -o /tmp/tg_test download/exp038_telegram/Telegram.apk
   grep -aE "EXP088-PHASE-B|UI-EVENT|lambda.*createView|presentFragment|LoginActivity.*<init>" /tmp/tg_test.log
   ```
5. After M is PROVEN (full login chain), campaign is complete.

## GitHub delivery status
- last_commit: 36c61cc9690f899faaf75402413f48323daad965
- remote_head: 36c61cc9690f899faaf75402413f48323daad965
- push_verified: true

## Reproducibility
- Telegram: 3/3 reproducible runs (identical screenshot SHA)
- All A4 tests pass
- All Phase F tests pass: 23/23
- All multi-DEX inject tests pass: 2/2
- All F5 return-wide tests pass: 5/5
- All regression tests pass: A1, B, B2, C, F, I — no regressions
