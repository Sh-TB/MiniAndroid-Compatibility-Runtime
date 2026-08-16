# EXP-050 Current State

**Date:** 2026-08-17
**Commit:** 3931464
**Execution Command:** `timeout 30 ./build_exp042/miniandroid_exp042 download/exp038_telegram/Telegram.apk run/exp050_returnval`

## Current Metrics

| Metric | EXP-049 | EXP-050 | Delta |
|--------|---------|---------|-------|
| Unique methods | 200 | **336** | **+136** |
| JNI calls | 5 | 5 | — |
| HALT-LOOP | 0 | 6 | +6 |
| HALT-GOTO | 0 | 0 | — |
| Memory peak | 440 MB | 452 MB | +12 MB |
| Result | SUCCESS | SUCCESS | — |
| SharedPreferences files | 0 | **1** | +1 |

## Key Breakthrough: Return Value Propagation

**Root cause:** `move-result` and `move-result-object` were returning placeholder
values (0 and null) instead of the actual return value from the last invoke-*
instruction. This silently discarded ALL return values from ALL method calls.

**Fix:** Added `last_invoke_return_` member, set by every invoke-* handler,
read by move-result/move-result-object.

**Impact:** +136 new methods, reaching deep into LaunchActivity:
- checkCurrentAccount, setupActionBarLayout, checkLayout, handleIntent
- updateCurrentConnectionState, checkFrameMetrics, checkSystemBarColors
- EmptyBaseFragment.createView
- FingerprintController (checkKeyReady, getKeyStore, isKeyReady)
- BuildVars (isBetaApp, hasDirectCurrency, useInvoiceBilling)
- DynamicAnimation (SpringAnimation, SpringForce)
- Many AndroidX credentials and Play Services classes

## SharedPreferences Persistence PROVEN

`runtime/data/org.telegram.messenger/shared_prefs/default.xml` was generated
by Telegram's own code via `edit().putBoolean().commit()`!

The XML contains real Telegram preference keys with real values.

## HALT-LOOP Events (6)

| Method | PC | Op | Cause |
|--------|----|----|-------|
| BaseFragment.getLastStoryViewer | 0x14 | invoke-static | Loop on story viewer check |
| SpringAnimation.sanityCheck | 0x27 | invoke-static | Animation validation loop |
| LifecycleRegistry.enforceMainThreadIfNeeded | 0x2e | invoke-static | Thread check loop |
| DynamicAnimation.startAnimationInternal | 0x30 | invoke-static | Animation start loop |

All are loops caused by missing API return values or missing thread state.

## Reached Telegram Methods (187 unique)

### LaunchActivity Deep Methods
- checkCurrentAccount (150 insns) — account management
- setupActionBarLayout (384 insns) — UI layout setup
- checkLayout (280 insns) — layout validation
- handleIntent (13 insns) — intent handling
- updateCurrentConnectionState (67 insns) — connection state
- checkFrameMetrics (42 insns) — frame metrics
- checkSystemBarColors (8+9 insns) — system bar colors
- getMainContainerFrameLayout (3 insns)
- getBottomSheetTabsOverlay (3 insns)

### Application Layer
- ApplicationLoader.startAppCenter, startAppCenterInternal
- ApplicationLoader.isStandalone, isHuaweiBuild, isHuaweiStoreBuild
- BackupAgent.requestBackup
- BuildVars.isBetaApp, hasDirectCurrency, useInvoiceBilling, isHuaweiStoreApp

### Controllers
- FingerprintController.checkKeyReady, getKeyStore, isKeyReady
- MediaController.setBaseActivity
- MessagesController.getGlobalMainSettings
- LiteMode.addOnPowerSaverAppliedListener

### UI
- EmptyBaseFragment.createView
- LayoutHelper.getSize
- RLottieNative.createFromRawJson
- BaseFragment.getLastStoryViewer (HALT-LOOP)

### Utilities
- AndroidUtilities.enableEdgeToEdge, isKeyguardSecure, removeFromParent

## Checkpoints

| Checkpoint | Status |
|-----------|--------|
| A: LaunchActivity entered | ✅ |
| B: LaunchActivity completed | ✅ |
| C: Application initialized | ✅ |
| D: UserConfig initialized | ✅ |
| E: SharedPreferences read | ✅ |
| F: NativeLoader reached | ✅ |
| G: First native dispatched | ✅ |
| H: SharedPreferences written | ✅ (default.xml generated!) |
| I: Login UI state | ❌ (checkCurrentAccount reached, but LoginActivity not yet) |

## Next Blockers

1. **HALT-LOOP in enforceMainThreadIfNeeded** — ArchTaskExecutor.isMainThread
   returns false, causing loop. Fix: make isMainThread return true.
2. **HALT-LOOP in SpringAnimation** — animation validation loop
3. **LoginActivity** — checkCurrentAccount is reached, which switches accounts.
   Need to trace what happens after isClientActivated check.
4. **More native methods** — still only native_getCurrentTime dispatched
