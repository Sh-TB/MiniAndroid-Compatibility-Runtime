# EXP-060 Phase 0 — Baseline (EXP-059 final state)

**Date:** 2026-08-19
**Build commit:** `c92d914` (EXP-059 final)
**Goal:** Establish a forensic baseline before any EXP-060 code changes.

## Run Configuration

- APK: `download/exp038_telegram/Telegram.apk` (Telegram 12.9.2, 82.7 MB)
- Binary: `build_exp042/miniandroid_exp042`
- Output dir: `run/exp060_baseline/`
- Duration: ~8.4 seconds

## Baseline Metrics (EXP-059 final state)

| Metric | Value |
|--------|-------|
| Total instructions executed | 50,221 |
| Unique methods | 558 |
| Unique classes | 232 |
| HALT events | 0 |
| EXCEPTION events | 16 |
| CLASS_INIT events | 64 |
| `[FRAGMENT-LIFECYCLE]` events | 16 |
| `setParentLayout` calls | 8 |
| `createView` calls (real subclass) | 4 |
| `onResume` calls | 6 |
| `setOnClickListener` calls | 0 ← NOT YET REACHED |
| `Handler.post` calls | 0 |
| Heap objects | ~3,000 |
| Peak RSS | ~503 MB |

## Verified Execution Frontier (EXP-059)

```
LaunchActivity.onCreate ✅
  → getIntent() → non-null Intent ✅
  → isClientActivated() → returns 1 ✅
  → getClientNotActivatedFragment() → returns IntroActivity ✅
      (LoginActivity.loadCurrentState returns empty Bundle on first launch)
  → addFragmentToStack(IntroActivity, -1) → returns TRUE ✅
  → IntroActivity.onFragmentCreate ✅
  → BaseFragment.setParentLayout (polymorphic dispatch to IntroActivity) ✅
  → ActionBarLayout.attachView ✅
  → IntroActivity.createView (608 code units) ✅
  → IntroActivity.attachSheets ✅
  → IntroActivity.onResume ✅
  → IntroActivity.onBecomeFullyVisible ✅
```

## IntroActivity Methods Reached

- `<init>` (29 bytes) — constructor
- `onFragmentCreate` (118 bytes) — sets up 6 intro slides
- `createView` (608 bytes) — builds ViewPager + BottomPagesView + RLottieImageView × 6
- `checkContinueText` (223 bytes) — updates "Continue" button text
- `onResume` (39 bytes)
- `updateColors` (188 bytes)
- `access$1800` (3 bytes) — accessor

## IntroActivity Inner Classes Reached

- `IntroActivity$1` (10 bytes) — anonymous class
- `IntroActivity$2` (6 bytes)
- `IntroActivity$3` (6 bytes)
- `IntroActivity$4` (20 bytes) — most likely the OnClickListener
- `IntroActivity$IntroAdapter` (4/6 bytes) — ViewPager adapter
- `IntroActivity$$ExternalSyntheticLambda1/2/3` — lambdas

## What's Missing (the EXP-060 target)

1. **No `setOnClickListener` calls observed** — the click handler is registered in
   `IntroActivity.createView` or `IntroActivity$4.<init>`, but the runtime never
   sees the call. Need to investigate why (View.setOnClickListener may be
   stubbed to no-op, or the click setup may be in a code path not yet reached).
2. **No `Handler.post` calls observed** — Runnable queuing not exercised.
3. **No navigation event** — Fragment transition from IntroActivity → LoginActivity
   is not triggered because no click event has been dispatched.

## EXP-060 Strategy

Per the mission:
- Do NOT directly call `LoginActivity`.
- DO implement a generic event system.
- DO dispatch a synthetic CLICK on the IntroActivity's "Start Messaging" button.
- DO let Telegram's real callback code execute the navigation.
- DO follow the actual navigation path (Fragment transaction / `presentFragment` / etc.).

## Reproducibility

Single run captured. Output preserved in `run/exp060_baseline/`.
