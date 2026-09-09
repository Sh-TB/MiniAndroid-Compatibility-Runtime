# CAMPAIGN 014 / MASTER-4 — FINAL SESSION REPORT

Session: 2026-09-09 (S14 continuation) · HEAD at report: `8de5382b` (unpushed, no credentials)
Baseline inherited: `f60634e4` clean; battery 54/54; DOOZ blocked at Material3 `LG0/b.<clinit>` ISE.

---

## 1. HEAD STATE

| Item | Value |
|---|---|
| Repo HEAD | `8de5382b` — "M4 F-028h+F-029: AtomicReferenceArray law + core reflection law" |
| Working tree | clean (artifacts auto-committed separately) |
| Battery | **79/79 ALL PASS** (`run_test_battery.sh`, fresh run, zero FAIL) |
| Commits this session | `8de5382b` (F-028h + F-029) — on top of `e2e91928` (UUID auto-commit carrying unproven F-028 code) |
| Environment rebuilt | aapt2 2.20-14304508 (Google Maven), dooz `d81292cd…` EXACT pin, HelloWorldSelfAware `009b4671…` EXACT pin, com.emmanuelmess.tictactoe_3 `760fe5ac…` EXACT pin |

Gossip eliminated on entry: `run/dooz_f028/report.md` claimed "SUCCESS ✅ 7.91 MB screenshot" — actual file
was byte-identical (sha `31ddd4d5…`) to the three known-blank baselines, **0 non-white pixels**, no run.log.
Report-generator rc-based status is not evidence; framebuffer is.

## 2. GENERIC FIXES (LAW → ROOT CAUSE → FIX → MICRO PROOF → REAL APK EFFECT)

### F-028 — untyped-register conversion law (inherited unproven → PROVEN this session)
* **LAW**: Dalvik registers are untyped 32/64-bit slots; the opcode defines the source interpretation.
  `const/high16` float bits tagged INT32 (`0x42E60000`) must read as `115.0f` through
  float-to-int / float cmp / float arith — never as the numeric int word `1120702464`.
* **ROOT CAUSE**: `CONV_SRC_F32`/`CONV_SRC_I32`/cmp/arith sites numeric-converted or bit-aliased
  raw bits across register tags. First real hit: dooz Material3 `LG0/b.<clinit>` fontScale
  table keys → ISE "You should only apply non-linear scaling to font scales > 1".
* **FIX**: `dalvik_raw_bits32()` reinterpretation at every listed site (F-028, committed in `e2e91928`).
* **MICRO PROOF**: `tests/fixtures/f028_float_law` (ECJ+D8 real DEX) — **7/7 bands GREEN** incl. the
  exact dooz key pattern; battery stage + pixel golden.
* **REAL APK EFFECT**: dooz fontScale ISE **gone**; Snapshot readError **gone** (both layers peeled).

### F-028h — AtomicReferenceArray law
* **LAW**: `java.util.concurrent.atomic.AtomicReferenceArray` elementwise get/set/getAndSet/
  compareAndSet/lazySet over a fixed-length grid; reference identity; fresh cell reads null.
* **ROOT CAUSE**: no engine implementation existed. kotlinx.coroutines `SegmentedQueue`/`Segment`
  (`b2/m`,`b2/n` — the Recomposer work queue) stores slots through it: enqueue `set()` was silently
  dropped (×1), dequeue `get()` returned null forever (**×629,769**), `_state` pinned at `0x40000000`.
* **FIX**: `AtomicShadow` array family (initially unreachable — `dispatch()` early guard rejected the
  class; guard extended with `is_ref_array`).
* **MICRO PROOF**: `[ATOMIC-DIAG] ARR-CAS` forensics prove law semantics: `cell(k=0 EMPTY) expect(k=0
  INT) → FAIL` is the correct AOSP verdict (null ≠ boxed Integer).
* **REAL APK EFFECT**: dooz run **completes for the first time** (report generated, 0 errors); the
  livelock moved out of the queue machinery into honest scheduler territory.

### F-029 — core reflection law
* **LAW**: `Class.getDeclaredMethod/getMethod/getDeclaredConstructor/getConstructor` mint
  Method/Constructor records; `Method.invoke` dispatches the reflected identity back through the
  bridge (recursive `bridge_to_api`, receiver-shifted, heap `array[i]` varargs);
  `Constructor.newInstance` runs the REAL DEX `<init>` when the class has a DEX body
  (FIX-M3-012b Room law preserved), bridge `<init>` otherwise.
* **ROOT CAUSE**: AndroidX `HandlerCompat.createAsync` (dooz `X1/h.<clinit>`, API ≥ 28 branch)
  reflects `Handler.createAsync(Looper)`; null Method/invoke → `M1/i.d` Intrinsics NPE inside
  clinit → composition killed. `AbstractComposeView.f` also needed `View.getHandler()`.
* **FIX**: bridge reflection core + **F-029a** `Handler.createAsync` → main Handler singleton;
  **F-029b** `View.getHandler()` → main Handler (ViewRootImpl law).
* **MICRO PROOF**: microtimer corpus run rc=0 SUCCESS; battery EXT/G stages green.
* **REAL APK EFFECT**: dooz X1/h clinit completes; AbstractComposeView attach chain proceeds.

### REGRESSION CAUGHT + RECONCILED (honesty record)
F-029 v1 intercepted the legacy `Constructor.newInstance` shim (read `__reflect_class`, skipped the
DEX ctor) and broke the microtimer Room path: 5 uncaught exceptions past the app boundary, run
downgraded to PARTIAL, battery 77/79. Fixed by dual-law reconciliation (dual field spellings
`class_desc` + `__reflect_*`, real DEX `<init>` via `try_recursive_invoke`). microtimer back to
**rc=0 SUCCESS, 0 uncaught**; battery back to **79/79**.

## 3. REAL-APK RESULTS TABLE (PHASE D matrix)

T-scale: T0 load · T1 launch · T2 lifecycle · T3 execute · T4 UI tree · T5 pixels ·
T6 interaction · T7 state change · T8 persistence · T9 deterministic replay.

| APK | Prior baseline | Current tier @ `8de5382b` | Δ | First blocker |
|---|---|---|---|---|
| HelloWorldSelfAware 1.1.0 | T7 (EXT-01/02 goldens) | **T7** — EXT-01 typography 9/9 + EXT-02 interaction 12-check PASS; frame 99.1% non-white | PRESERVED | — |
| dubrowgn.microtimer_8 | T8 (F-012 persistence) | **T8** — SUCCESS, 50.2% non-white, F-012 two-pair persistence+byte-determinism PASS | PRESERVED | — |
| omegacentauri.simplestopwatch_26 | battery PASS | **T5+** — SUCCESS, 110,185 non-white px | PRESERVED | — |
| de.duenndns.gmdice_8 | battery PASS | **T5+** — SUCCESS, 1,744,539 non-white px (84%) | PRESERVED | — |
| io.github.yamin8000.dooz_18 | PARTIAL blank, ISE at Material3 | **T3→T4 frontier** — composition now constructs **past Material3 Typography + Recomposer creation**; halts inside coroutine scheduler; framebuffer 0 non-white | **3 blocker layers peeled** (fontScale ISE, SegmentedQueue livelock, reflection NPE) | `LY1/j;.j` Segment CAS-retry — honest wait-for-other-thread |
| com.emmanuelmess.tictactoe_3 | T3/BLANK (libGDX GL boundary) | **T3** — rc=0 SUCCESS, 0 non-white px | PRESERVED | GLSurfaceView/libGDX render boundary |
| tictactoe_golden (fixture) | §29 interaction+determinism | **T9** — §29 PASS (tap → state → frame diff, 3-run SHA determinism) | PRESERVED | — |

Central question — "does the strategy shift make MiniAndroid more compatible with real apps?" —
answered by executable evidence: **yes for the blocker classes hit this session** (float untyped
registers, atomic arrays, framework reflection are app-agnostic layers under Compose-era APKs);
**preserved-equal** for the six corpus APKs (no regressions; one introduced regression was caught
and reconciled within the session); dooz gained 3 peeled layers but has not crossed to pixels.

## 4. PHASE B — TICTACTOE HISTORICAL FORENSIC VERDICT

**Classification: PARTIALLY VERIFIED — VERIFIED-PRESERVED (fixture) / UNVERIFIED-BY-DESIGN (real APK).**

* The historical "agent plays tic-tac-toe" claim binds to **`tictactoe_golden`**
  (`com.miniandroid.tictactoegolden`, View-based fixture APK, ECJ+D8, introduced `de5f370e`
  2026-09-05) — NOT to the real `com.emmanuelmess.tictactoe_3`.
* Artifact audit (`docs/evidence/tictactoe_golden/`): `frames_manifest.json` — 9 clicks requested,
  9 dispatched (listener-kind), per-frame `changed_pixels_vs_previous` (e.g. 2,741 px between
  moves), visible text "X to move"; `board_launch.png` / `board_x_wins.png` — 2,023,282 / 2,023,183
  non-white pixels (real renders).
* Current HEAD: battery §29 **PASS** (interaction + 3-run determinism) → historical success is
  **preserved**, not regressed and not beautified.
* Real `com.emmanuelmess.tictactoe_3` (sha `760fe5ac…` EXACT G09 pin, re-run this session):
  rc=0, 0 non-white px — honest **T3/BLANK** at the libGDX/GLSurfaceView boundary; records never
  claimed otherwise.

## 5. PHASE E — CROSS-APK BLOCKER RANKING

| # | Blocker | APKs affected | Semantic centrality | Reproducibility | Solvability |
|---|---|---|---|---|---|
| 1 | **Single-threaded coroutine scheduler pump** (lock-free SegmentedQueue/EventLoop spins need queue-driven progress at HALT-LOOP boundaries) | dooz now; Telegram/WhatsApp/Signal class of apps (kotlinx everywhere) | highest — every modern APK's async core | deterministic (HALT-LOOP logs) | subsystem-sized (law: pump Handler/Looper queue at spin boundaries, then retry frame) |
| 2 | GLSurfaceView/libGDX render boundary | real tictactoe, game corpus | medium (games segment) | deterministic | law-sized (GL surface → framebuffer bridge) |
| 3 | Long-tail View/Context REC-MISSes | long tail | low | per-APK | incremental |

## 6. ACQUISITION HONESTY (PHASE C limits)

Telegram / WhatsApp / Signal APKs were hash-verified at acquisition in the prior session
(f5e11927… / 56c3717b… / 82a2cb99…) but the cache outside `my-project` was wiped by the container
restart; re-download attempts this session did not complete (CDN unreachability). No C1–C7 claims
are made for them at this HEAD beyond the recorded acquisition hashes — no fabrication.

## 7. NEXT SPOTLIGHT

**Dispatcher-pump law** (blocker #1): at HALT-LOOP detection inside coroutine scheduler methods,
pump the deterministic Handler/Looper queue (run pending posted continuations) before force-return,
so the "other thread" of a lock-free handshake exists on the single deterministic thread. This is
the last law-shaped gap between dooz's constructed composition and the first framebuffer pixels.
