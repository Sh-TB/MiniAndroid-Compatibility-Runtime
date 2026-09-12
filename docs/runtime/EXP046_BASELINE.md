# EXP-046 Baseline — Telegram Execution State

**Date:** 2026-08-16
**Commit:** 7f17602
**Reproduced:** 2026-08-16

## Execution Metrics

| Metric | Value |
|--------|-------|
| Unique methods | 154 |
| HALT-LOOP | 0 |
| HALT-GOTO | 0 |
| Memory peak | 440 MB |
| Execution time | <30s (completes naturally) |
| Result | SUCCESS |
| Exit code | 0 |

## Top 10 Methods by Call Count

| Calls | Method |
|------:|--------|
| 5,048 | Theme.getColor |
| 1,164 | LinearLayoutCompat.<init> |
| 199 | AppCompatCheckBox.<init> |
| 45 | AndroidUtilities.dp |
| 39 | Intrinsics.checkNotNullParameter |
| 24 | TintTypedArray.getInt |
| 21 | RLottieDrawable.scheduleNextGetFrame |
| 21 | RLottieDrawable.ignoreScheduleNextGetFrame |
| 21 | RLottieDrawable.getFramesCount |
| 21 | RLottieDrawable.canLoadFrames |

## Native Boundary

- **NativeLoader.initNativeLibs** was reached in previous EXP-045 runs
- 462 native methods discovered across 5 DEX files
- 44 P0 (startup path) native methods
- First native candidate: `ConnectionsManager.native_getCurrentTime(I)I`
- JNI bridge: NOT YET IMPLEMENTED

## Checkpoints

| Checkpoint | Status |
|-----------|--------|
| A: LaunchActivity.onCreate entered | ✅ |
| B: LaunchActivity.onCreate completed | ✅ |
| C: Application initialization | ✅ |
| D: UserConfig initialized | ✅ |
| E: SharedPreferences accessed | ✅ (bridge returns singleton) |
| F: NativeLoader reached | ✅ |
| G: First native method dispatched | ❌ |
| H: Login UI initialized | ❌ |
