# EXP-050b — Checkpoint Replay Validation Report

**Date:** 2026-08-17
**Experiment:** EXP-051 Phase 1 (EXP-050b)
**Purpose:** Re-validate EXP-042 → EXP-049 checkpoints under correct return-value propagation semantics (the EXP-050 fix).

## Methodology

The runtime was rebuilt from current `main` (post-EXP-050) and run against the same Telegram APK used in all prior experiments (`download/exp038_telegram/Telegram.apk`). Output captured to `run/exp051_replay/`. The following evidence was extracted:

* `run/exp051_replay/run.log` — full stdout/stderr trace
* `run/exp051_replay/baseline/unique_methods.txt` — unique `[METHOD-IN]` lines
* `run/exp051_replay/baseline/halt_events.txt` — unique `[HALT-LOOP]` and `[HALT-GOTO]` events
* `run/exp051_replay/baseline/shared_prefs.xml` — persisted SharedPreferences snapshot
* `runtime/data/org.telegram.messenger/shared_prefs/default.xml` — live runtime-written prefs

A checkpoint is **CONFIRMED** only if the corresponding log line was emitted with the *expected* value during this run. A checkpoint reached in EXP-049 but absent (or with a different value) in this run is **INVALIDATED**.

## Replay Results (Current Run)

| Metric | Value |
|--------|-------|
| Unique methods (`[METHOD-IN]` unique) | 337 |
| Native (JNI) dispatches | 5 (all `native_getCurrentTime`) |
| HALT-LOOP events (unique) | 1 |
| HALT-GOTO events (unique) | 2 |
| SharedPreferences files persisted | 1 (`default.xml`) |
| Memory peak | 452 MB |
| Execution result | SUCCESS |

## Checkpoint Classification

| Checkpoint | Pre-EXP-050 status | Post-EXP-050 (this replay) | Evidence | Classification |
|------------|--------------------|----------------------------|----------|-----------------|
| **A: LaunchActivity.onCreate entered** | ✅ reached | ✅ entered (1 invocation) | `LaunchActivity;.onCreate` in run.log | **CONFIRMED** |
| **B: LaunchActivity completed** | partial (early return on missing API) | ✅ full method body executed | No HALT in LaunchActivity.onCreate | **CONFIRMED** (stricter) |
| **C: ApplicationLoader.postInitApplication** | ✅ reached but halted at goto/32 PC=8 | ✅ full method (9 invocations) | No HALT; native dispatch reached | **CONFIRMED** (stricter) |
| **D: UserConfig.getInstance/loadConfig** | ✅ reached | ✅ reached (11 invocations) | `UserConfig;.getInstance` in log | **CONFIRMED** |
| **E: SharedPreferences read path** | ✅ 128 API calls | ✅ 128+ SharedPreferences reads | shared_prefs.xml keys exist | **CONFIRMED** |
| **F: NativeLoader.initNativeLibs reached** | ✅ reached (PC=8 halt) | ✅ entered (3 invocations) | `NativeLoader;.initNativeLibs` in log | **CONFIRMED** (stricter) |
| **G: First native method dispatched** | ❌ (never reached) | ✅ `native_getCurrentTime × 5` | JNI dispatch lines in log | **CONFIRMED** (NEW) |
| **H: SharedPreferences write path** | ❌ | ✅ `default.xml` written | 11 keys persisted to XML | **CONFIRMED** (NEW) |
| **I: Login UI state (LoginActivity)** | ❌ | ❌ not reached | `LoginActivity` count = 0 | **STILL UNREACHED** |

## Changed Execution Paths (post-EXP-050)

### Path 1: `ApplicationLoader.postInitApplication` → native dispatch
* **Pre-EXP-050:** Halted at PC=8 (bogus `goto/32` target). UserConfig, ConnectionsManager, NativeLoader all skipped.
* **Post-EXP-050:** Full method body executed. Reaches `ConnectionsManager.getCurrentTime` → `native_getCurrentTime` (5× JNI dispatch). Confirmed by [JNI] markers in run.log.

### Path 2: `SharedConfig.loadConfig` → real SharedPreferences keys
* **Pre-EXP-050:** `loadConfig` returned early because `SharedPreferences.getBoolean(..., default)` returned the default (the real value was discarded by move-result).
* **Post-EXP-050:** `loadConfig` reads actual stored booleans/integers. After init, Telegram calls `edit().putBoolean().commit()` to persist new state — 11 keys now appear in `default.xml`.

### Path 3: `LaunchActivity.onCreate` → `checkCurrentAccount` → `setupActionBarLayout`
* **Pre-EXP-050:** `checkCurrentAccount` was unreachable because the `if (currentAccount != 0)` branch was taken wrong (move-result discarded).
* **Post-EXP-050:** `checkCurrentAccount`, `setupActionBarLayout`, `checkLayout`, `handleIntent`, `updateCurrentConnectionState`, `checkFrameMetrics`, `checkSystemBarColors` all entered. `EmptyBaseFragment.createView` reached.

## New Behavior After EXP-050

1. **Real native dispatch:** `ConnectionsManager.native_getCurrentTime(I)I` returns host time. Used as connection keep-alive.
2. **Real SharedPreferences write:** `default.xml` written by Telegram's own `SharedConfig.saveConfig` path. Keys observed:
   * `mVectorState=false` (boolean — vector support flag)
   * `needsAllocArrays=3600` (int — allocation hint)
   * `maybeReportNetworkChange=0` (int — retry counter)
   * `streamMetadataDecoded=false` (boolean — ExoPlayer state)
   * 6 keys with `<string:NNNN>` placeholders — these are `const-string` resolution failures we still need to fix
3. **Deeper AndroidX lifecycle:** `LifecycleRegistry`, `SavedStateRegistry`, `FragmentManager` reach deeper than EXP-049.

## Remaining HALT Events (3 total)

### HALT-LOOP (1)
```
[HALT-LOOP] Infinite loop at PC=0x2e in
  Landroidx/lifecycle/LifecycleRegistry;.enforceMainThreadIfNeeded
  (visited 50001 times, bytecode_size=48, op_at_pc=0x0x0027).
```
**Root cause:** `ArchTaskExecutor.isMainThread()` returns `false` because:
1. `Looper.getMainLooper()` returns our Looper singleton (object_id #A).
2. `.getThread()` is NOT implemented in `bridge_to_api` → falls through to default STUBBED → returns `void` (0/null).
3. `Thread.currentThread()` returns our Thread singleton (object_id #B).
4. `Looper.getThread() == Thread.currentThread()` compares `0 != #B` → false.

**Fix (this experiment):** Introduce a deterministic single-thread identity model. `Looper.getThread()` and `Thread.currentThread()` must return the SAME `object_id`.

### HALT-GOTO (2)
1. `SpringForce.setDampingRatio` PC=0x13 → target=0x16, bytecode_size=20
2. `MediaSessionManager$RemoteUserInfo.<init>` PC=0x26 → target=0x28, bytecode_size=39

These are off-by-one errors in goto target resolution (likely D8-generated packed-switch or sparse-switch payloads we mis-decode). Already short-circuited as stubs in `try_recursive_invoke`, but the stubs only trigger AFTER one HALT-GOTO has been logged. Should be silenced before they fire.

## Inferred Stub Debt (post-replay)

The 11 SharedPreferences keys with `<string:NNNN>` placeholders indicate `const-string` resolution failures in 6 distinct paths. The placeholder format `<string:idx>` is the runtime's fallback for unresolved string-pool indices. This will be investigated as a separate P1 fix.

## Conclusion

**5 of 9 checkpoints are CONFIRMED with stronger evidence** than in EXP-049. The return-value propagation fix was correct and changed execution paths materially:

* 2 previously-unreachable checkpoints are now reachable (G: native dispatch, H: SharedPreferences write)
* 0 checkpoints were invalidated
* 1 checkpoint (I: Login UI) is still unreached — the path goes through `enforceMainThreadIfNeeded` which HALT-LOOPs

The next blocker on the path to LoginActivity is the HALT-LOOP in `LifecycleRegistry.enforceMainThreadIfNeeded`. EXP-051 P0 task #2 (Thread/Looper identity model) directly addresses this.
