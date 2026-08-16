# EXP-049 Current State

**Date:** 2026-08-17
**Git Commit:** 654c3bd
**Execution Command:** `timeout 30 ./build_exp042/miniandroid_exp042 download/exp038_telegram/Telegram.apk run/exp049_baseline`

## Current Metrics

| Metric | Value |
|--------|-------|
| Unique methods | 189 |
| JNI calls | 5 (native_getCurrentTime × 5) |
| JNI unsupported | 0 |
| HALT-LOOP | 0 |
| HALT-GOTO | 0 |
| Memory peak | 440 MB |
| Execution time | ~3.4s |
| Result | SUCCESS (exit 0) |

## Reached Methods (189 unique)

### Telegram Core (45 methods)
- LaunchActivity.onCreate (1330 insns)
- ApplicationLoader.postInitApplication (266 insns)
- SharedConfig.loadConfig (1278 insns), buildVersion, loadDebugConfig
- UserConfig.getInstance, loadConfig (492 insns), getCurrentUser, isClientActivated
- ConnectionsManager.getInstance, getCurrentTime
- MessagesController.getInstance, putUser (430 insns)
- MessagesStorage.getInstance, getUnsentMessages
- SendMessagesHelper.getInstance, checkUnsentMessages
- ContactsController.getInstance, checkAppAccount
- DownloadController.getInstance
- BillingController.getInstance, isReady, startConnection
- LocaleController.getInstance
- MediaController.getInstance
- NativeLoader.initNativeLibs (234 insns)
- SharedPrefsHelper.init
- FileLog.d, FileLog.e
- DispatchQueue.cancelRunnable, postRunnable
- DispatchQueuePoolBackground.execute (5 + 91 insns)
- AccountInstance.getMessagesStorage
- BaseController.getMessagesStorage
- SaveToGallerySettingsHelper.load, SharedSettings.read/save/access
- SharedConfig$BackgroundActivityPrefs.access$002
- BitmapsCache.recycle, decrementTaskCounter

### Telegram UI (19 methods)
- Theme: createChatResources (2441), createCommonResources (753), createDialogsResources (878), createCommonMessageResources (536), createCommonChatResources (684), createCommonDialogResources (79), createProfileResources (56), applyCommonTheme (362), applyProfileTheme (41), addChatPaint (15), reloadAllResources (35), destroyResources (1), getColor (6+7), getNonAnimatedColor (7)
- RLottieDrawable: <init> (115), canLoadFrames (24), scheduleNextGetFrame (98), checkChoreographer (9), checkRunningTasks (34), hasParentView (23), invalidateInternal (45), beginApplyLayerColors (4), commitApplyLayerColors (40), requestRedrawColors (37), recycle (44), recycleNativePtr (24), recycleResources (37), setAllowDecodeSingleFrame (8), setLayerColor (13), ignoreScheduleNextGetFrame (14), getFramesCount (6)
- LinkPath.getRadius, getRoundedEffect
- PathAnimator.addSvgKeyFrame (266)
- PremiumGradient.getInstance, checkColors, checkIconColors

### Telegram Network (7 methods)
- ConnectionsManager.getInstance, getCurrentTime
- SerializedData.readInt32, cleanup
- TLObject.TLdeserialize
- TLRPC$help_AppUpdate.TLdeserialize
- TLParseException.doThrowOrLog

### AndroidX Lifecycle (20 methods)
- ComponentActivity.onCreate, initializeViewTreeOwners, setContentView
- FragmentActivity.onCreate
- FragmentController.dispatchCreate
- FragmentHostCallback.getFragmentManager
- FragmentManager.dispatchCreate
- FragmentManagerViewModel.setIsStateSaved
- LifecycleRegistry.handleLifecycleEvent, moveToState, enforceMainThreadIfNeeded
- Lifecycle$Event.getTargetState, Lifecycle$State.isAtLeast
- ReportFragment.injectIfNeededIn, registerIn, <init>, LifecycleCallbacks
- SavedStateRegistry.performAttach, performRestore
- SavedStateRegistryController.performAttach, performRestore
- ArchTaskExecutor.getInstance, isMainThread
- ViewTree* (LifecycleOwner, ViewModelStoreOwner, SavedStateRegistryOwner, OnBackPressedDispatcherOwner, FullyDrawnReporterOwner)

### AndroidX AppCompat (20 methods)
- LinearLayoutCompat.<init> (5+123), setBaselineAligned, setDividerDrawable
- AppCompatCheckBox.<init>
- ActionMenuView.<init>
- TintTypedArray.<init>, obtainStyledAttributes, getBoolean, getDimensionPixelSize, getDrawable, getFloat, getInt, getWrappedTypeArray, recycle
- ResourceManagerInternal (12 methods): get, getDrawable, createCacheKey, createDrawableIfNeeded, getCachedDrawable, loadDrawableFromDelegates, installDefaultInflateDelegates, checkVectorDrawableSetup, tintDrawable, getTintList, getTintListFromCache, getTintMode, addDelegate, addTintListToCache
- DrawableUtils: canSafelyMutateDrawable, fixDrawable, forceDrawableStateChange
- AppCompatResources.getDrawable
- ContextCompat.getDrawable
- DrawableCompat: setTintList, setTintMode, wrap

### AndroidX Collections (7 methods)
- SimpleArrayMap: <init> (7+24), get, put (143), indexOf (82), indexOfKey, indexOfNull, isEmpty
- ArrayMap.<init>
- SparseArrayCompat.get, SparseArrayCompatKt.commonGet
- ContainerHelpersKt.binarySearch

### Kotlin Intrinsics (6 methods)
- checkNotNullParameter (6 insns) — 39 calls
- checkNotNullExpressionValue (32 insns)
- throwParameterIsNullNPE (16 insns) — stubbed
- createParameterIsNullExceptionMessage (89 insns) — stubbed
- sanitizeStackTrace (11+37 insns) — stubbed

### Other (4 methods)
- DesugarCollections.synchronizedMap
- ConcurrentHashMap.<init> (4+7 insns)
- com.android.billingclient.api.zzce.<init>

## Reached Android APIs

### Context
- getApplicationContext → singleton
- getResources → Resources singleton
- getPackageName → "org.telegram.messenger.web"
- getSharedPreferences → per-name SharedPreferences object
- getFilesDir → File singleton
- getCacheDir → File singleton
- getApplicationInfo → ApplicationInfo singleton
- getSystemService → null
- getExternalFilesDir → File singleton
- getMainLooper → Looper singleton

### Resources
- getDisplayMetrics → DisplayMetrics (density=1.0, 1080x1920)
- getConfiguration → Configuration (screenLayout=0x40)
- getColor → 0xFF000000 (black)
- getIdentifier → 0 (not found)
- getDimensionPixelSize → 24

### SharedPreferences (128 API calls via invoke-interface)
- getBoolean × 68
- getInt × 36
- getString × 8
- getLong × 8
- contains × 3
- getSharedPreferences × 5

### System
- currentTimeMillis → real Unix time
- nanoTime → real monotonic time

### Window
- setFlags → void (no-op)
- getDecorView → View singleton

### Handler/Looper
- getMainLooper → Looper singleton
- Handler.<init>/post/postDelayed/removeCallbacks → void (no-op)

### Other
- Log.d/i/w/e → int
- File.<init>/getAbsolutePath/exists/mkdirs
- Thread.currentThread/getStackTrace → singleton/empty array
- PackageManager.getPackageInfo → PackageInfo (versionCode=9999)

## Reached Native Methods

| Class | Method | Signature | Calls | Status |
|-------|--------|-----------|-------|--------|
| ConnectionsManager | native_getCurrentTime | (I)I | 5 | HOST_COMPATIBILITY_STUB |

## JNI Bridge Registered Stubs (12)

| Class | Method | Signature | Status |
|-------|--------|-----------|--------|
| ConnectionsManager | native_getCurrentTime | (I)I | HOST_STUB |
| ConnectionsManager | native_getCurrentTimeMillis | ()J | HOST_STUB |
| ConnectionsManager | native_getTimeDifference | (I)I | HOST_STUB |
| ConnectionsManager | native_getCurrentPingTime | (I)I | HOST_STUB |
| ConnectionsManager | native_getCurrentDatacenterId | (I)I | HOST_STUB |
| ConnectionsManager | native_getConnectionState | (I)I | HOST_STUB |
| ConnectionsManager | native_init | (I)I | HOST_STUB |
| ConnectionsManager | native_setJava | (Z)V | HOST_STUB |
| ConnectionsManager | native_isTestBackend | (I)Z | HOST_STUB |
| NativeLoader | init | (Ljava/lang/String;Z)V | HOST_STUB |
| NativeByteBuffer | native_free | (I)V | HOST_STUB |
| NativeByteBuffer | native_limit | (I)I | HOST_STUB |

## Unresolved Blockers

1. **SharedPreferences write path** — SharedConfig.loadConfig only reads, doesn't write. Need to find edit().putString().commit() call path.
2. **More native methods** — Only native_getCurrentTime dispatched. Need deeper execution for native_init, native_setJava.
3. **Login UI** — LaunchActivity.onCreate completes but doesn't reach LoginActivity/IntroActivity.
4. **invoke-interface routing** — Fixed in EXP-048, but need to verify ALL invoke-* opcodes route correctly.
5. **Method overload resolution** — Currently uses arg count, needs descriptor-aware resolution.

## Known Technical Debt

| ID | Item | Status |
|----|------|--------|
| TD-001 | throwParameterIsNullNPE stubbed | TEMPORARY |
| TD-002 | createParameterIsNullExceptionMessage stubbed | TEMPORARY |
| TD-003 | sanitizeStackTrace stubbed | TEMPORARY |
| TD-004 | FragmentManager.dispatchStateChange stubbed | TEMPORARY |
| TD-005 | runOnUIThread/executeOnUIThread stubbed | TEMPORARY |
| TD-006 | ContextAwareHelper.dispatchOnContextAvailable stubbed | TEMPORARY |
| TD-007 | FragmentStore methods stubbed | TEMPORARY |
| TD-008 | TransactionInactiveError stubbed | TEMPORARY |
| TD-009 | Google identitycredentials stubbed | TEMPORARY |
| TD-010 | Theme.getColor returns black | TEMPORARY |
| TD-011 | Context.getSystemService returns null | TEMPORARY |
| TD-012 | Resources.getIdentifier returns 0 | TEMPORARY |
| TD-013 | Resources.getDimensionPixelSize returns 24 | TEMPORARY |
| TD-014 | Window.setFlags is no-op | TEMPORARY |
| TD-015 | DynamiteModule.load returns null | TEMPORARY |
