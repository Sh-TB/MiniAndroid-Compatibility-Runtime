# EXP-046 Progress Summary

**Date:** 2026-08-17
**Commit:** fd1de55

## Execution Metrics

| Metric | EXP-045 (baseline) | EXP-046 (current) | Change |
|--------|-------------------|-------------------|--------|
| Unique methods | 154 | 184 | +30 |
| HALT-LOOP | 0 | 0 | — |
| HALT-GOTO | 0 | 0 | — |
| Memory peak | 440 MB | 440 MB | stable |
| Execution time | <30s | <30s | — |
| Result | SUCCESS | SUCCESS | — |

## Key Breakthroughs

### 1. Per-DEX Field Resolution
Root cause: Same as BLOCKER-033 (per-DEX method_idx) but for fields. The merged DexReport concatenates field_ids from all 5 DEX files, so per-DEX field_idx points to wrong fields.

Fix: `resolve_field()` now uses per-DEX raw DEX bytes to resolve field_idx correctly.

### 2. JNI Bridge Infrastructure
- `src/jni/jni_bridge.h` — header-only JNI bridge with 12 registered native method stubs
- Native method dispatch integrated into `try_recursive_invoke()`
- JNI bridge initialized before execution in `application_runtime.cpp`

### 3. NativeLoader.nativeLoaded Pre-population
Pre-populated `NativeLoader.nativeLoaded=true` to allow `initNativeLibs` to proceed past the loaded check.

### 4. Native Method Analysis
- 462 native methods across 5 DEX files
- 44 P0 (startup path) native methods
- JNI loading boundary: `System.loadLibrary("tmessages.49")` at initNativeLibs PC=13
- First native candidate: `ConnectionsManager.native_getCurrentTime(I)I`
- Native methods NOT yet dispatched (System.loadLibrary is stubbed)

## New Methods Reached (30 more)

### Telegram Core
- `SharedConfig.loadConfig` (1278 insns) — full config loading
- `SharedConfig.buildVersion`, `loadDebugConfig`
- `SaveToGallerySettingsHelper.load` (157 insns), `.save` (77 insns)
- `BillingController.startConnection` — billing init
- `MediaController.getInstance` — media init
- `LocaleController.getInstance` — locale init
- `AndroidUtilities.isFold` — foldable detection

### Previously reached (confirmed stable)
- `NativeLoader.initNativeLibs` (234 insns)
- `UserConfig.getInstance`, `isClientActivated`
- Full Theme system (createChatResources 2441 insns)
- Full RLottieDrawable lifecycle
- Full AndroidX lifecycle (FragmentActivity, FragmentManager, LifecycleRegistry)
- Full AppCompat UI (LinearLayoutCompat, TintTypedArray, ResourceManagerInternal)

## Checkpoints

| Checkpoint | Status |
|-----------|--------|
| A: LaunchActivity.onCreate entered | ✅ |
| B: LaunchActivity.onCreate completed | ✅ |
| C: Application initialization | ✅ |
| D: UserConfig initialized | ✅ |
| E: SharedPreferences accessed | ✅ |
| F: NativeLoader reached | ✅ |
| G: First native method dispatched | ❌ (JNI bridge ready, native calls not reached) |
| H: Login UI initialized | ❌ |

## Next Blocker

The execution reaches `System.loadLibrary("tmessages.49")` but the call is stubbed (returns void). Native methods are never dispatched because:
1. `System.loadLibrary` is stubbed → no .so loading → no JNI_OnLoad → no RegisterNatives
2. `ConnectionsManager.getInstance` (which calls `native_getCurrentTime`) is not yet reached

The next step is to either:
1. Pre-register native methods (bypass System.loadLibrary)
2. Make execution go deeper to reach ConnectionsManager.getInstance
3. Implement System.loadLibrary to at least log the attempt and register stubs
