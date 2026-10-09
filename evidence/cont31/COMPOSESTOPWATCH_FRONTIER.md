# CONT-31 — composeStopwatch Re-Supply, R-NEW-466 On-Lineage Verdict, and F-NEW-289 Main-Queue Delivery Identity Root

Wave: CONT-31 (user directive: ادامه). Predecessor: evidence/cont30w (the
white-screen claim audit). This wave: (1) re-supplied the R-NEW-466 target APK
from F-Droid and tested the R-NEW-466 claims ON this lineage; (2) recovered the
container reset (56-commit chain restored from origin/main, binary rebuilt
byte-exact); (3) found, root-caused, fixed, and regression-proved the FIRST
genuine composeStopwatch divergence (F-NEW-289).

## 0. CONTAINER RESET RECOVERY (before any work)

The local clone was found STALE at the CONT-10-era lineage (6a66806a) with a
machine tmp-snapshot commit (e99c2fbd) on top; the binary and run/ artifacts
were gone; the CONT-30W push (837f68e4) was absent locally. Recovery:

- `git fetch origin` → remote main = **837f68e4** (the full 56-commit chain
  intact: `6a66806a..origin/main` = 56 commits).
- `git branch backup-reset-snapshots e99c2fbd` (tmp-only snapshots preserved),
  then `git reset --hard origin/main` → HEAD = 837f68e4.
- Verified: `m3_payload_parts` present (F-NEW-286 fix), evidence/cont30w
  present, registry 597 rows.
- Rebuild from HEAD: foreground `timeout 570 make -j1 BUILD_DIR=build` →
  **b84114cd6f8bad1d byte-exact** == the CONT-30 record (source-faithful).
- Simple Calculator re-supplied again (tmp wiped): `68da25fd9fdf54b4` SHA-exact.

## 1. composeStopwatch RE-SUPPLIED (R-NEW-466 target)

| item | value |
|---|---|
| APK | `com.justdeax.composeStopwatch` v1.9.1, versionCode 1009011 |
| source | F-Droid repo (`https://f-droid.org/repo/...`), API-verified |
| SHA-256 | `dbf937ebbe7c0b3d24c07fa0ede7cb53ea117f7071db3b61f1c96b7d257cda55` |
| note | the R-NEW-466 report recorded NO APK SHA; same package, version on their side unknown (honest) |

## 2. R-NEW-466 RUNTIME CLAIMS — VERDICTS UPGRADED ON THIS LINEAGE

R-NEW-466 (ServiceLoader iterator dispatch fix) was tested on THIS lineage with
zero preconceptions (baseline binary b84114cd6f8bad1d, no engine change):

| R-NEW-466 claim | verdict on THIS lineage | evidence |
|---|---|---|
| "Main dispatcher is missing" ISE occurs | **REJECTED** — never occurs | full logs csw_r1..r3: zero Main-dispatcher exceptions |
| `l5` = AndroidDispatcherFactory materializes | **CONFIRMED** — and WITHOUT their patch | `[S102-SERVICELOADER] load kotlinx.coroutines.internal.MainDispatcherFactory … next -> l5 obj#948` |
| `t5` = AndroidExceptionPreHandler materializes | **CONFIRMED** — and WITHOUT their patch | `[S102-SERVICELOADER] load kotlinx.coroutines.CoroutineExceptionHandler … next -> t5 obj#5462` |
| DataStore exception is the next frontier | **CONFIRMED** (DataStore ENOENT present, deferred/handled) | `preference.preferences_pb (ENOENT)` first-run, caught |
| Their dedicated-iterator fix is needed | **REJECTED for this lineage** | current main's F-NEW-252-wave ServiceLoader law (self-as-iterator + both-typed dispatch + shadow decline) delivers the same materialization; CONT-30W already proved the probe-level law |

The R-NEW-466 report's before-state (Main dispatcher missing) does not
reproduce on this lineage — it belongs to the other worktree's base. Its fix is
NOT transplanted (directive law).

## 3. FIRST GENUINE composeStopwatch DIVERGENCE (pre-fix, binary b84114cd6f8bad1d)

Baseline ×3 deterministic: rc=1, screenshot `5c4a0172628849ba` ×3,
verdict `DEFAULT_BACKGROUND_ONLY`, **ISE "Cannot invoke setValue on a
background thread" ×60 per run**.

Ground-truth chain (androguard disasm + runtime trace):

1. App starts worker threads (`Lcn;` Thread-subclass executor, oids 5379/5384)
   — DataStore/coroutines IO shape; bodies run via `run_thread_start_body`
   which binds the F-110d worker identity for the run-to-completion window.
2. INSIDE the body the coroutine machinery posts the Dispatchers.Main
   continuation to the main MessageQueue (Runnable 5399), then the worker
   PARKS (`LockSupport.park`).
3. The R-NEW-345 park law (`drain_park_queues_bounded`,
   dalvik_engine.cpp:24502) drains the main queue AT the park boundary —
   **nested inside the worker's F-110d identity window** — and executed the
   continuation with the WORKER identity.
4. The continuation chain `Lf;.p → La21;.j/.r → Lb21;.c → Lio;.j → Lse;.j →
   Lu4;.W → Llw;.T → Ld;.d/.p → Lcm0;.i → Lcm0;.a` reaches LiveData.setValue's
   assert `Lcm0;.a` (= LiveData.assertMainThread, R8-collapsed:
   `IllegalStateException("Cannot invoke " + name + " on a background thread")`).
5. The assert's check `Lca;.P()Z` (= R8-renamed
   androidx.arch.core.executor.DefaultTaskExecutor.isMainThread; ground truth:
   `Looper.getMainLooper().getThread() == Thread.currentThread()`) answered
   FALSE — the delivery inherited the worker identity.
6. ISE ×60/run; caught at `Llw;.T` catch-all; the app's state chain died
   before content; `Lh4;` (the Compose-backed custom view) onDraw dispatched
   with **ops=0** → `DEFAULT_BACKGROUND_ONLY` frame.

**Semantic law violated (AOSP Looper/Handler model)**: code delivered by the
main Looper's MessageQueue ALWAYS executes on the main thread. A worker posts
and returns; the main Looper delivers on ITS OWN thread. The deterministic
engine's park-drain delivered the main-queue Runnable while the worker
identity was still bound — a real identity the app can legitimately observe.

## 4. F-NEW-289 — ROOT_CAUSED_FIXED (minimal generic fix)

**Root**: main-MessageQueue deliveries executed with the inherited worker
identity when the drain ran nested inside a worker thread's run-to-completion
body.

**Fix** (one semantic root; save/restore mirroring
`run_thread_start_body`'s F-110d pattern; no-op when identity is already
main):

- `drain_park_queues_bounded` arm 1 (main-queue runnables) — dalvik_engine.cpp
  ~24556-24566: re-bind `active_drained_thread = 0` (main) around each
  delivery, restore after.
- `drain_park_queues_bounded` arm 2 (Choreographer doFrame) — ~24584-24594:
  same law (doFrame is a main-looper delivery).
- `ExecutionEngine::invoke_handler_runnable` + `invoke_choreographer_do_frame`
  (execution_engine.cpp): same root at the remaining main-delivery entries —
  no-op today (the fnew289 v1 probe proved those sites drain with main
  identity), uniform law for future call paths.

No package checks, no app-specific logic, no exception suppression, no forced
rendering. Worker bodies keep the F-110d worker identity (the BODY-WORKER
control row proves it).

## 5. PROBE — fixtures/fnew289_probe (real aapt2/ECJ/D8)

Isolates exactly the handoff: a Thread-subclass worker posts a Runnable to the
main Handler, then `LockSupport.parkNanos` — the coroutines "post continuation,
park worker" shape. Rows:

| row | asserts | pre-fix | post-fix |
|---|---|---|---|
| BODY-WORKER | inside body: currentThread != main (F-110d) | PASS | PASS ×3 |
| QUEUE-MAIN | inside main-queue Runnable: currentThread == main | **FAIL** (divergence isolated) | **PASS ×3** |
| LOP-MAIN | inside Runnable: myLooper == mainLooper | PASS | PASS ×3 |
| SUMMARY | | FAIL 2/1 | **PASS 3/0 ×3** (28/0 PASS rows in the battery count) |

Post-fix battery record: `PROBE fnew289 rc=1 PASS=28 FAIL=0`.

## 6. TARGET APP AFTER THE FIX — honestly PARTIAL

composeStopwatch ×3 on the fixed binary `9bdd61328d0f01d9`:

| run | rc | screenshot | ISE count | verdict |
|---|---|---|---|---|
| csw_post_r1 | 1 | `5c4a0172628849ba` | **0** (was 60) | DEFAULT_BACKGROUND_ONLY |
| csw_post_r2 | 1 | `5c4a0172628849ba` | **0** | DEFAULT_BACKGROUND_ONLY |
| csw_post_r3 | 1 | `5c4a0172628849ba` | **0** | DEFAULT_BACKGROUND_ONLY |

- The LiveData main-thread ISE is ELIMINATED (deterministic ×3).
- The frame is UNCHANGED — the divergence MOVED, as required by honesty:
  the next frontier is a NEW, distinct face:
  `IllegalStateException: "Dialog has no window"` at `Lea;.r pc=2` (depth 53),
  caught by catch-alls in `Lx30;.n` (multiple try ranges) — the app now
  reaches a dialog-show path that never executed before. Recorded as the
  NEXT-WAVE target; NOT attributed to F-NEW-289 beyond the identity law.
- Deferred faces unchanged (honest): R350-FORNAME
  (kotlin.reflect ReflectionFactoryImpl CNFE), S102-CLASSLOADER
  (AndroidCompositionLocals_androidKt CNFE — a REAL androidx class name worth
  a dedicated look next wave), DataStore ENOENT.
- No content-pixel claims (the Lh4; view still paints ops=0).

## 7. REGRESSION GATE — ZERO DRIFT at 9bdd61328d0f01d9

scripts/cont31_regression.sh (full gate — the binary CHANGED this wave):

| gate | result |
|---|---|
| anchors ×3 ×8 apps | dooz `d602648e8e401895`, microtimer `da73010a37dd0189`, unote `4f1a9e4e8f64fae8`, gmdice `f3b483fe7b7cf51b`, opencalc `a976d2f9fb675cb3`, tttdeluxe `af6094295ecb50e3`, flappycow `13cf47464d9787f4`, g2048 `59ca1526611c4622` — **24/24 BYTE-IDENTICAL MATCH** |
| probe battery | fcol 140/0, f259 49/0, f259g 84/7 (known-honest F259-L row), f266 42/0, f268 96/0 — **== CONT-28/29/30 records EXACTLY** |
| standing battery (rebuilt) | fnew253 **147/0**, fnew286 **10/0**, fnew252 **56/0** (ServiceLoader positive row healthy with the CONT-30W packaging fix) |
| new probe | fnew289 **28/0** |
| Track B control | Simple Calculator ×3 rc=0 `7960bce447ac6d8f` — FULL SUCCESS retained |

All probe APKs rebuilt fresh (run/ artifacts were lost in the container reset).

## 8. STATUS WORDS

- F-NEW-289: **ROOT_CAUSED_FIXED / TESTED / OBSERVED** (probe + target ISE
  elimination + zero-drift regression).
- composeStopwatch rendering: **PARTIAL** — divergence moved to the
  "Dialog has no window" face; no app-owned content pixels claimed.
- R-NEW-466 on this lineage: claims verdicts per §2; the patch itself stays
  untransplanted (not needed here).
- Registry: 597 → **598** (F-NEW-289 added; dedup-checked against 289-free).

## 9. NEXT RESUMABLE CHECKPOINT

1. The "Dialog has no window" ISE (`Lea;.r`, depth 53) — decode `Lea;` /
   `Lx30;` from the APK DEX, establish which dialog path composeStopwatch
   reaches, and whether the dialog's window was never created (engine gap) or
   created-then-lost.
2. `AndroidCompositionLocals_androidKt` CNFE — a REAL androidx.compose.ui
   platform class name failing resolution; check why the class resolver misses
   it (it may gate the Compose locals table and the ops=0 face).
3. Standing: F-NEW-288 (TextUnit spin, P0) for the oracle Track A; Simple
   Calculator input-pump for Track B.
