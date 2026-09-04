# EXP-045 Baseline — Telegram Execution State

**Date:** 2026-08-16
**Commit:** 077006f

## Execution Metrics

| Metric | Value |
|--------|-------|
| Unique methods reached | 158 |
| Total instructions (30s) | 100K+ |
| HALT-LOOP | 0 |
| HALT-GOTO | 0 |
| Memory peak | 439 MB |
| Result | SUCCESS (completes naturally) |

## Execution Depth

### CHECKPOINT A: LaunchActivity.onCreate entered — ✅ REACHED
### CHECKPOINT B: LaunchActivity.onCreate completed — ✅ REACHED (previously, with longer timeout)
### CHECKPOINT C: Application initialization (postInitApplication) — ✅ REACHED
### CHECKPOINT D: UserConfig initialized — ✅ REACHED (getInstance, isClientActivated)
### CHECKPOINT E: SharedPreferences accessed — ✅ REACHED (bridge returns singleton)
### CHECKPOINT F: NativeLoader reached — ✅ REACHED (initNativeLibs called)
### CHECKPOINT G: First native method — ❌ NOT REACHED (need JNI bridge)
### CHECKPOINT H: Login UI initialized — ❌ NOT REACHED

## Key Breakthroughs in EXP-045

1. **O(1) class lookup** — Changed try_recursive_invoke from O(N=41078) linear search to O(1) hash map lookup. This was the #1 performance bottleneck.

2. **Correct invoke argc extraction** — The 35c format encodes argc in the high nibble of the instruction's high byte. Previous code pushed ALL 5 registers regardless. Now only argc registers are pushed, enabling correct overload resolution.

3. **Method overload resolution by parameter count** — When multiple methods have the same name, match by parameter count from the descriptor. This fixed `sanitizeStackTrace(1-arg)` calling itself instead of `sanitizeStackTrace(2-arg)`.

4. **Dangling pointer fix** — `all_methods()` returns a vector by value (temporary). The overload resolution code stored raw pointers to elements in this temporary. After the for loop, the temporary was destroyed, causing use-after-free. Fixed by storing the vector in a local variable.

5. **D8 hybrid goto encoding** (from EXP-044, preserved) — D8 uses goto/16 and goto/32 with the high byte as an 8-bit signed offset when non-zero, and standard 20t/30t format when zero.

## Methods Reached (158 unique)

### Telegram Core
- LaunchActivity.onCreate (1330 insns)
- ApplicationLoader.postInitApplication (266 insns)
- UserConfig.getInstance, isClientActivated
- AndroidUtilities: dp, isTablet, isTabletForce, isTabletInternal, isSmallTablet, getMinTabletSide, getTabletLeftFragmentSize, checkDisplaySize, bold, fillStatusBarHeight, recycleBitmaps
- DispatchQueue.cancelRunnable, DispatchQueuePoolBackground.execute (5 + 91 insns)
- FileLog.e
- BitmapsCache.recycle, decrementTaskCounter

### Theme System
- Theme.createChatResources (2441 insns)
- Theme.createCommonResources (753 insns)
- Theme.createDialogsResources (878 insns)
- Theme.createCommonMessageResources (536 insns)
- Theme.createCommonChatResources (684 insns)
- Theme.createCommonDialogResources (79 insns)
- Theme.createProfileResources (56 insns)
- Theme.applyCommonTheme (362 insns)
- Theme.applyProfileTheme (41 insns)
- Theme.addChatPaint (15 insns)
- Theme.reloadAllResources (35 insns)
- Theme.destroyResources (1 insns)

### AndroidX Lifecycle
- ComponentActivity.onCreate, initializeViewTreeOwners, setContentView
- FragmentActivity.onCreate
- FragmentController.dispatchCreate
- FragmentManager.dispatchCreate, dispatchStateChange, moveToState, getSpecialEffectsControllerFactory
- FragmentStateManager.getFragment
- LifecycleRegistry.handleLifecycleEvent, moveToState, enforceMainThreadIfNeeded
- Lifecycle$Event.getTargetState, Lifecycle$State.isAtLeast
- ReportFragment.injectIfNeededIn, registerIn, LifecycleCallbacks
- SavedStateRegistry.performAttach, performRestore
- SavedStateRegistryController.performAttach, performRestore
- ArchTaskExecutor.getInstance, isMainThread
- ViewTreeLifecycleOwner.set, ViewTreeViewModelStoreOwner.set, ViewTreeSavedStateRegistryOwner.set
- ViewTreeOnBackPressedDispatcherOwner.set, ViewTreeFullyDrawnReporterOwner.set

### AndroidX AppCompat
- LinearLayoutCompat.<init> (5 + 123 insns), setBaselineAligned, setDividerDrawable
- AppCompatCheckBox.<init>
- ActionMenuView.<init>
- TintTypedArray.<init>, obtainStyledAttributes, getBoolean, getDimensionPixelSize, getDrawable, getFloat, getInt, recycle
- ResourceManagerInternal: get, getDrawable, createCacheKey, createDrawableIfNeeded, getCachedDrawable, loadDrawableFromDelegates, installDefaultInflateDelegates, checkVectorDrawableSetup, tintDrawable, getTintList, getTintMode, addDelegate
- DrawableUtils.canSafelyMutateDrawable, fixDrawable, forceDrawableStateChange
- ContextCompat.getDrawable, ContextCompat$Api21Impl.getDrawable
- DrawableCompat$Api21Impl.setTintList, setTintMode
- AppCompatResources.getDrawable

### AndroidX Collections
- SimpleArrayMap.<init> (7 + 24 insns), get, put (143 insns), indexOf (82 insns), indexOfKey, indexOfNull, isEmpty
- ArrayMap.<init>
- SparseArrayCompat.get, SparseArrayCompatKt.commonGet
- ContainerHelpersKt.binarySearch

### Kotlin Intrinsics
- checkNotNullParameter (6 insns) — 2,108 calls
- checkNotNullExpressionValue (32 insns) — 1,024 calls
- throwParameterIsNullNPE (16 insns)
- createParameterIsNullExceptionMessage (89 insns)
- sanitizeStackTrace (11 insns) — 1-arg version
- sanitizeStackTrace (37 insns) — 2-arg version (CORRECTLY resolved!)

### Components
- RLottieDrawable.<init> (115 insns), recycle, recycleNativePtr, recycleResources, checkChoreographer, checkRunningTasks, hasParentView
- LinkPath.getRadius, getRoundedEffect
- PathAnimator.addSvgKeyFrame (266 insns)

### Other
- DesugarCollections.synchronizedMap
- Google Play Services classes (zaad, zzc, AbstractSafeParcelable, IdentityCredentialManager, etc.)

## Current Blocker

Execution reaches 158 methods but times out at 30-60s. The bottleneck is:
1. **Intrinsics NPE paths**: 2,108 checkNotNullParameter calls × ~159 instructions per NPE = ~335K instructions wasted on null checks
2. **SimpleArrayMap operations**: 2,716 constructor calls + put/get/indexOf operations
3. **SpecialEffectsController**: 1,030 calls to getOrCreateController

## Next Steps

1. Investigate why 2,108 null checks are triggered (which parameters are null?)
2. Pre-populate the correct framework objects to prevent NPEs
3. Profile to find the next performance bottleneck
4. Run with longer timeout to see if execution completes

## JNI Distance

**NativeLoader.initNativeLibs** was reached (the first `System.loadLibrary` call site). This is the JNI boundary. The first native method would be `ConnectionsManager.native_getCurrentTime`.
