# EXP-045 Final Status — Telegram Execution Breakthrough

**Date:** 2026-08-16
**Commit:** e72885a
**Result:** LaunchActivity.onCreate COMPLETES SUCCESSFULLY in <30s

## Execution Metrics

| Metric | EXP-044 (start) | EXP-045 (final) | Change |
|--------|----------------|-----------------|--------|
| Unique methods | 43 | 154 | +111 (3.6x) |
| HALT-LOOP | 0 | 0 | — |
| HALT-GOTO | 20 | 0 | -20 (eliminated) |
| Memory peak | 440 MB | 440 MB | stable |
| Execution time | timeout (60s) | <30s (completes) | breakthrough |
| NPE checks/call | ~159 insns | ~7 insns | 23x faster |

## Key Fixes (in order of impact)

1. **O(1) class lookup** (class_info_index_) — Changed try_recursive_invoke from O(N=41078) linear search to O(1) hash map. #1 performance bottleneck.

2. **Correct invoke argc extraction** — 35c format encodes argc in high nibble. Previous code pushed ALL 5 registers. Now only argc registers are pushed, enabling correct overload resolution.

3. **Method overload resolution** — Match by parameter count from descriptor. Fixed sanitizeStackTrace(1-arg) calling itself instead of (2-arg).

4. **Dangling pointer fix** — all_methods() returns temporary vector. Stored in local var to keep alive.

5. **D8 hybrid goto encoding** — goto/16 and goto/32 use high byte as 8-bit offset when non-zero. Eliminated ALL 20 HALT-GOTO events.

6. **Type-aware if-ltz** — D8 uses if-ltz for null checks on OBJECT_REF (branch if non-null) and numeric checks on INT32 (branch if < 0).

7. **Array bounds checking** — aget-object simulates ArrayIndexOutOfBoundsException for out-of-bounds access.

8. **NPE path stub** — Stubbed throwParameterIsNullNPE, createParameterIsNullExceptionMessage, sanitizeStackTrace. Reduced NPE cost from 159 to 7 instructions per check.

9. **FragmentManager.dispatchStateChange stub** — Broke infinite Fragment state change loop.

10. **Various stubs** — runOnUIThread, ContextAwareHelper, FragmentStore, TransactionInactiveError, Google credentials.

## Checkpoints Reached

| Checkpoint | Status |
|-----------|--------|
| A: LaunchActivity.onCreate entered | ✅ |
| B: LaunchActivity.onCreate completed | ✅ |
| C: Application initialization | ✅ |
| D: UserConfig initialized | ✅ |
| E: SharedPreferences accessed | ✅ |
| F: NativeLoader reached | ✅ |
| G: First native method | ❌ (need JNI bridge) |
| H: Login UI initialized | ❌ (need UI rendering) |

## Methods Reached (154 unique)

### Full AndroidX Lifecycle
ComponentActivity, FragmentActivity, FragmentController, FragmentManager,
LifecycleRegistry, ReportFragment, SavedStateRegistry, ArchTaskExecutor

### AppCompat UI
LinearLayoutCompat (123-insn constructor), TintTypedArray, ResourceManagerInternal,
DrawableUtils, DrawableCompat, ContextCompat, ViewCompat, AppCompatResources

### Collections
SimpleArrayMap (init, get, put, indexOf, isEmpty), ArrayMap,
SparseArrayCompat, ContainerHelpersKt.binarySearch

### Telegram Theme System
createChatResources (2441 insns), createCommonResources (753),
createDialogsResources (878), applyCommonTheme (362), getColor (5K+ calls)

### RLottie Animation
RLottieDrawable.<init> (115 insns), canLoadFrames, scheduleNextGetFrame (98 insns),
setLayerColor, commitApplyLayerColors, invalidateInternal, requestRedrawColors

### Other
PremiumGradient, LinkPath, PathAnimator, FileLog, DispatchQueue,
BitmapsCache, UserConfig, AndroidUtilities

## Next Blocker

The execution COMPLETES successfully but the next major boundary is:
1. **JNI bridge** — NativeLoader.initNativeLibs was reached but native methods are not implemented
2. **UI rendering** — View hierarchy not constructed (need View, ViewGroup, Canvas)
3. **Persistence** — SharedPreferences not wired to real storage
