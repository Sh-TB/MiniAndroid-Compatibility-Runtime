# S20 EXECUTION GATE REPORT — baseline, targets, bottlenecks, plan (2026-11-21)

**Status: PLANNING — no implementation started. Awaiting Main Coder approval.**
Repo: Sh-TB/MiniAndroid-Compatibility-Runtime @ main. Author: the audit agent (S3–S20 session chain).

---

## 1. Current HEAD and working-tree status (verified this session)

| Item | Value |
|---|---|
| HEAD | `2466a240` — "S20 closeout — REGRESSION_RESULTS.md regenerated in v2.5" |
| Parent | `3358d97b` — "S20 — #632 registry audit COMPLETE: 234/234" |
| Branch | `main`, working tree **clean** (0 tracked modifications), pushed to origin |
| Disk | 6.4 GB free; `build/` **absent** (sandbox recycle wipes it) |
| Toolchain | g++ (Debian) 14.2.0, GNU make, **nproc = 2**; `/usr/bin/time` ABSENT; **no ccache/distcc/lld/mold installed** |
| Battery at HEAD | 52 law-test binaries (102 test sources; last full run S19: 52/52 rc=0) |

Note: the directive says "Seven remaining census rows" — that was true at S19 close; the S20 audit closure (`3358d97b`) has since settled them (234/234, comment `7063417383`). This does **not** change the Main Coder's core point: zero of that work touched runtime code.

## 2. S19/S20 changes that are genuinely active in the runtime: **NONE**

- `git diff --stat 3cfb3786~1..2466a240 -- src/` = **empty** — no runtime source changes in S19 or S20.
- S19 commit `3cfb3786` changed 14 files: `Makefile` (2 lines: registering the new test binary), `tests/s19_grid_scroll_laws_test.cpp` (+122, a **test**), evidence CSVs/MDs, 2 RAW_LOGS, 3 scripts. All documentation/tests/scripts/planning.
- S20 (`3358d97b`+`2466a240`): registry stamps, ledger AUD-63, digest section, deliverables v2.5, fetch/stamp scripts. No src/.
- Live-vs-dormant verification (the directive's requirement, done at HEAD):
  - `core_sources.manifest` drives compilation (`CORE_SOURCES := $(shell grep -v '^\#' core_sources.manifest)`); `make -n build/miniandroid` confirms `software_renderer.cpp` and `vector_decode.cpp` **are compiled** (live).
  - `Makefile:624-631 DORMANT_SOURCES` = api_dispatcher, exception_system, execution_guard, execution_observatory, **view_renderer.cpp**, real_layout.cpp (+ `dalvik_engine.cpp` monolith when `DALVIK_SPLIT=1`, which is the default — the 94K-line monolith is the *fallback*, the 5 split TUs `dalvik_engine_{core,invoke,opcodes,bridge,tail}.cpp` are the live path).
  - **Nothing cited below references dormant code.**

## 3. Five evidence-backed APK targets

All failures below are already reproduced in existing evidence (no new claims). Sources: `APK_REGISTRY.json` (UNIFIED_011 statuses), `evidence/w21/runtime_baseline.tsv` (15 APKs × runs, measured), W21 `runtime_perf/*_r*/report.md` + `lifecycle_trace.json`, S210 logs.

| # | Package / title | Original source | Current observed failure (reproduced) | First confirmed divergence / missing semantic | Expected behavior |
|---|---|---|---|---|---|
| T1 | `io.github.yamin8000.dooz` (Dooz, TicTacToe variant) | F-Droid repo `io.github.yamin8000.dooz_18.apk` (URL recorded in `tests/corpus/apks.json`) | ROOT-LOCATED — COMPOSE SNAPSHOT BOUNDARY (F-020): `ISE` from `SnapshotKt.readError` at `LP/l;.q`; `setContent`→`mutableStateOf` write chain proven via F-016 unwind forensics; blank frame | Compose **snapshot state read/write semantics** absent; S210 further root-caused post-nav blank-white to corrupted kotlinx `Segment` state (slot-queue) → `AbortFlowException` → ART process-death law → place pass never runs | Interactive tic-tac-toe board (2-player + AI), rendered and tappable |
| T2 | `org.kirkezz.rttt` (RTTT) | F-Droid package page (URL to be pinned — task T0) | SUCCESS rc=0 ×1, **empty frame** — registry: "Compose frontier family" | Same family as T1: Compose UI pipeline runs to completion but renders nothing (background-only frame) | Rendered game UI |
| T3 | `de.saschahlusiak.freebloks` (Freebloks 3D board) | F-Droid package page (URL to be pinned — task T0) | Boots clean `onCreate→onResume`, 31 frames produced, verdict **DEFAULT_BACKGROUND_ONLY** (1-color `(48,48,48)`, sha16 `b5a7a35d5fe0564b`), `first_missing_stage=APP_DRAW_OPS` (registry s138) | The **draw-op walk** never runs: window/root background paints, then the View-draw op dispatch is missing | Board with pieces rendered; tappable |
| T4 | `com.itsfrz.tictactoe_5` | Handoff ZIP set (`upload/handoff_apks/com.itsfrz.tictactoe_5.apk`, sha in W21 baseline) | Lifecycle reaches **RESUMED** (W21 trace), then an `ISE` escapes the app boundary at `MainActivity.onCreate`; empty frame | Unwind shows `Landroidx/navigation/fragment/NavHostFragment;.<init>` — **androidx navigation-fragment initialization** semantics missing | Menu/board rendered |
| T5 | `org.secuso.privacyfriendlydicer` | F-Droid package page (URL to be pinned — task T0) | Runs to `SplashActivity.onCreate`, `ISE` at app boundary, empty frame (registry) | Same androidx-boundary family as T4 (exact site to be re-confirmed on the fresh run) | Dice roller UI |

Spares (not in the five): `dev.lucanlm.antimine` (same T4/T5 class), `org.secuso.privacyfriendly2048` + `com.serwylo.lexica` (**540 s exec-budget timeout**, no frame — a Dalvik-throughput bottleneck, separately tracked). W21 blank=1.0 family (`com.attenomy.janken`, `com.ivylopez.authsrng`, `de.tcrass.minos`, `io.github.herrerad85.tallybook`, `org.ecos.logic.flip_a_coin`) — **SUSPECTED** Compose/draw-walk members (hypothesis until T0 re-runs them at HEAD).

**Local availability**: the handoff set holds only the 15 older W21 APKs — **none of T1–T3/T5 are cached locally**. Re-fetch goes through `scripts/download_test_apks.py` (zero-APK policy; SHA-verified; external cache outside the repo).

## 4. Three highest-impact shared execution-chain bottlenecks

Chain: APK → manifest/resources/DEX → Dalvik (split TUs) → framework semantics → lifecycle → ViewTree/layout → **rendering** → input. Verified live TUs only.

- **B2 — the APP_DRAW_OPS draw-walk gap (render pipeline stops after background)** — highest leverage. Evidence: freebloks T3 (`first_missing_stage=APP_DRAW_OPS`, face = background-only); every blank=1.0 frame in the W21 baseline is consistent with the same terminal state. Likely files (live): `src/renderer/software_renderer.cpp` (draw-op dispatch → raster), framework draw shadows (`android_shadows.cpp`), possibly the Canvas/RenderNode op-record path. One root-cause fix here plausibly moves **every blank-frame target**, which is why it ranks above the Compose work.
- **B1 — Compose snapshot/state frontier** — T1 (root-located, two independent analyses: F-020 `SnapshotKt.readError` ISE; S210 kotlinx `Segment` slot-queue corruption → `AbortFlowException` → process death) + T2. Files (live): dex split TUs + the state/snapshot shadow layer. Unlocks the Compose family (2 confirmed + several suspected members).
- **B3 — androidx boundary semantics (per-app family, one dispatch path)** — T4 (`NavHostFragment.<init>` unwind→escape) + T5 (+ dicerroller's `createWelcomeDialog` escape; antimine). Not one bug: a family of missing semantic ops sharing the androidx initialization/navigation/dialog dispatch path (`api` shadow layer). Fixed per-app after B2/B1; lowest per-line leverage.

Dormancy guard: none of these cite `view_renderer.cpp`; the split-dalvik default (`DALVIK_SPLIT=1`) is the live interpretation path.

## 5. Integration status of other coders' contributions (ledger-classified, 69 rows)

Per `ACHIEVEMENT_LEDGER.csv` (validator PASS): **INTEGRATED 27** (each with an active call path + a battery test; e.g. MG-011 `vector_decode.cpp:942` fail-honesty — IMPLEMENTED+TESTED), **PARTIALLY-INTEGRATED 5**, **NOT-INTEGRATED 10**, **DOCUMENTED-ONLY 7**, **BLOCKED 8**, **REJECTED-EXPERIMENT 8**, **SUPERSEDED-BY-SPLIT 1 + SUPERSEDED 2**, **N/A 6**.

Gate-relevant items:
- **#633 [MG-009]** (aapt2 string-referenced `pathData`): BLOCKED — implementable-with-fixture; the live read is `src/resources/vector_inflater.cpp:356`; needs a hand-built mini-ARSC/AXML fixture before any patch can carry a law test. **Not counted as integration.**
- **#634 [MG-012]** (animated-vector / drawable-document refs): BLOCKED — feature-class (no animated-vector branch; dormant copy rejects at `vector_decode.cpp:495-497`; no drawable-doc loader, grep=0). **Not counted as integration.**
- Isolated research/unmerged branches/documentation-only coder claims: PENDING/DOCUMENTED-ONLY — not runtime integration under this directive's definition.

## 6. Build-time baseline — MEASURED this session (exact commands)

All at HEAD `2466a240`, `make -j2`, default flags (`-std=c++17 -Wall -Wextra -g -O2 -MMD -MP`), 2 cores:

| Scenario | Command | Wall time | Notes |
|---|---|---|---|
| 1. Clean build | `rm -rf build && { time make -j2 all; }` | **6m38.4s** (user 9m26s) | 89 compile commands; binary `build/miniandroid` 119,784,752 B; link ends "Build complete", `anchors` step included |
| 2. No-change rebuild | `{ time make -j2 all; }` | **1.05s** | 0 compiles — `-MMD -MP` dep tracking honored, all objects reused |
| 2b. Second no-change | same | **1.047s** | stable |
| 3. One-TU incremental | `touch src/resources/layout_inflater.cpp && make -j2 all` | **11.98s** | exactly 2 commands: 1 TU recompile (large TU, ~10 s) + relink |
| 4. Link-only | extracted link command via `make -n build/miniandroid`, timed alone | **0.98s** | verified: binary mtime advanced |

**Diagnosis (fact):** the "repeated build delay" is **not** incremental-build pathology — dependency tracking and object reuse work (1.05 s no-change). The cost is the **cold build** (6m38) — 89 TUs at `-g -O2` on 2 cores, dominated by the large split-dex TUs — paid in full whenever the recycle wipes `build/`.

**Levers (hypotheses to be A/B-measured in the implementation phase, correctness preserved):**
1. `ccache` (not installed) — biggest expected cold-rebuild win after recycle wipes.
2. `-g1` default — already profiled in a separate W23 build profile (`build_p2a`, `Makefile:40` substitution exists but is profile-gated; default is still `-g`); the delta at HEAD is unmeasured.
3. Makefile wart: duplicate recipe for `build_p2a/dex/dalvik_interpreter.o` (Makefile:273 vs 289 "overriding recipe" warnings) — correctness cleanup.
**Measurement plan:** re-run the exact 4-scenario protocol above after each lever; same commands, same box; no disabling of deps/tests.

## 7. Proposed S20 task sequence (for approval — STOP before implementation)

| Task | Work | Expected proof (per Phase 6) | Est. |
|---|---|---|---|
| T0 baseline refresh | Pin/record original URLs for T2/T3/T5; re-fetch all 5 APKs (SHA-verified, external cache); re-run each at HEAD; capture rc / blank-ratio / frame sha16 / first divergence / lifecycle trace | Fresh baseline rows (tsv) + per-run logs; every later claim measured against THIS | 0.5 d |
| T1 = **B2 draw-walk** (top priority) | Reproduce T3's `APP_DRAW_OPS` stop → root-cause in the live draw path → one shared fix → focused law test + negative mutation → full battery | freebloks frame beyond background (frame sha change, blank-ratio drop, 3 independent runs, before/after + SHA-256 screenshots at fixed dimensions); **cross-impact check** on ≥2 blank-family apps from T0 | 1–2 d |
| T2 = **B1 Compose snapshot** | Reproduce T1 ISE at HEAD; implement the minimum snapshot read/write semantics law (write→read visibility, no `readError`); regression test + mutation | dooz passes the F-020 boundary (state update visible in trace; screenshot); RTTT non-empty frame; 3 runs each | 2–3 d |
| T3 build efficiency | Install ccache; A/B the 4-scenario protocol; decide `-g1` default from measurements; fix Makefile:273/289 duplicate recipe | The same measurement table before/after; battery unchanged-green | 0.5 d |
| T4 = **B3 androidx boundaries** (last — lowest leverage) | Per-target semantic fill (T4 NavHostFragment init; T5's exact site from the fresh run) with per-app contract tests | Each target passes its boundary; 3 runs; before/after frames | 1–2 d |
| Ride-along | NEW-26 one-liner (`text_shaper.cpp:619` `src.size()+1`→`src.size()`) with the s98 text laws guarding | Battery green incl. text laws | 0.1 d |
| Not in S20 | #633 (blocked on mini-ARSC fixture), #634 (feature-class), the exec-budget pair (2048/Lexica throughput) | — | — |

Priority rationale: **B2 first** because it is the earliest shared rendering failure across the whole blank-frame family (impact × N apps), then B1 (Compose family), then per-app B3 — impact, not ease.

## 8. Blockers on reliable measurement

1. **T1–T3/T5 APKs not cached locally** and T2/T3/T5 URLs not yet pinned in `tests/corpus/apks.json` (T1's URL is recorded) — resolved by task T0; without it no target can be re-reproduced.
2. **2-core sandbox, no ccache**: every full proof cycle (clean build 6m38 + battery build/run) costs ~10–25 min wall — budget accordingly; T0 fetches depend on network reachability to f-droid.org.
3. `/usr/bin/time` absent (bash `time` used — fine, noted for reproducibility).
4. **Hypotheses vs facts flagged**: the W21 blank=1.0 family's Compose membership is unverified per-app (suspected only); T5's exact ISE site is from registry text, to be re-confirmed on the fresh T0 run; B2's root-cause location inside the draw path is inferred from `first_missing_stage=APP_DRAW_OPS` + code reading, to be proven by T1's reproduction.
5. `freebloks`' expected behavior involves its GL renderer — the B2 fix must be verified against the software-raster path the engine actually takes (face evidence suggests it already renders via software_canvas).

---

**This report is the approval-gate deliverable. No implementation has been started.**
Facts above carry commit/file/line/test anchors; items marked SUSPECTED/hypothesis do not claim runtime truth until reproduced under task T0/T1/T2.
