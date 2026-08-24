# MiniAndroid Agent State — EXP-089 Campaign

## Current Experiment
EXP-089 — Continue Telegram Phase M after generic VM fixes

## Current Commit (most recent state)
HEAD — 7842e1e — CRITICAL FIX: invoke-static overload resolution for $r8$lambda methods
**PUSHED and VERIFIED: HEAD == origin/main == 7842e1e2bc77fd6b08b35d253e16141cd718a2b5**

## Status: 10 PROVEN, 1 IN PROGRESS (M boundary advanced — lambda$createView$1 SUCCEEDS)

### PROVEN (no change)
- A1 AXML inflation, A2 measure/layout, A5 text rendering, A4 drawable/image loading
- B1 valid PNG, B5 entry-point resolution, B generic input/click, B2 event dedup
- C SQLite, F Handler/Looper, I multi-DEX

### IN PROGRESS (M boundary advanced this round)

The invoke-static overload resolution fix unblocked the REAL "Start Messaging" path:

```
phase_b_click dispatches click on view 2488 (IntroActivity$4) ✅
→ listener = IntroActivity$$ExternalSyntheticLambda2
→ onClick executes (bytecode_size=6) ✅
→ invoke-static $r8$lambda$wAg5 (CORRECT method_idx=41198, not _-ElmO) ✅
→ $r8$lambda$wAg5 calls lambda$createView$1 via invoke-direct ✅
→ lambda$createView$1 try_recursive_invoke SUCCEEDED ✅
→ [lambda$createView$1 bytecode creates new LoginActivity(), calls setIntroView(), calls presentFragment()]
→ [next: verify LoginActivity object is created on heap]
```

### Root-cause fixes this round

1. **CRITICAL: invoke-static overload resolution for $r8$lambda methods**:
   - When method_name was already a D8-renamed `$r8$lambda$<hash>` name, the old code
     matched ANY method containing "lambda" and "$r8$lambda" — matching ALL D8 lambdas
   - The FIRST matching lambda (by iteration order) was picked, which was the WRONG one
   - This caused onClick(Lambda2) to execute `$r8$lambda$_-ElmO` (→ lambda$createView$2,
     the language switcher) instead of `$r8$lambda$wAg5` (→ lambda$createView$1, the
     "Start Messaging" button that calls presentFragment → LoginActivity)
   - FIX: When method_name starts with "$r8$lambda", require EXACT name match.
     Only fall back to substring matching for ORIGINAL names (lambda$...).

2. **phase_b_click now clicks ALL clickable views** (not just the first):
   - Previously only dispatched click on the first view (ActionBar back button)
   - Now iterates all 5 clickable views, dispatching click on each
   - Stops when a LoginActivity is created on the heap

3. **Enhanced EXP079-DIRECT diagnostics**:
   - Now traces lambda$new$0, presentFragment, swapToFragment, onBackPressed
   - Logs SUCCEEDED/FAILED for key lambda methods

## GitHub delivery status
- last_commit: 7842e1e2bc77fd6b08b35d253e16141cd718a2b5
- remote_head: 7842e1e2bc77fd6b08b35d253e16141cd718a2b5
- push_verified: true

## Reproducibility
- All A4 tests pass: 4/4
- All Phase F tests pass: 23/23
- All multi-DEX inject tests pass: 2/2
- All F5 return-wide tests pass: 5/5
- All regression tests pass: A1, B, B2, C, F, I — no regressions
