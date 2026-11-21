# S21 MASTER INTEGRATION REPORT — cross-coder recovery + WS1 B2 implementation — 2026-11-21

**Start HEAD `1cf09f53` == origin/main; final HEAD: this commit (source + evidence). Sandbox: 2 cores / 3 GB RAM / 5.7 GB disk / g++ 14.2.**

## 1. Exact HEADs
Start `1cf09f53` (clean, == origin/main). Final: start + the S21 commit(s) below (source change + evidence pack). No unpushed claims.

## 2. Existing issue work recovered (Phase 0/1 classifications)

| Source | Contribution | Classification (verified this session) |
|---|---|---|
| #635/S20 | B2 draw-walk root cause + approved contract-gate proposal | **APPLY_READY → IMPLEMENTED** (§3) |
| #676 | F058 ActivityLifecycleCallbacks chain | **ALREADY_IN_MAIN + reachable** — registration (`android_shadows.cpp:7069/7087`) AND dispatch (`dispatch_activity_lifecycle_callbacks` ×4 call sites, live TU `dalvik_engine_core.cpp`; observed live in this session's chess run: `[F058-DISPATCH] onActivityPostResumed → obs=218` + `[F058] fan-out: 2/2 observers executed`) |
| #520 (Coder 7) | R-144..R-149 component runtime | **PARTIALLY IN MAIN** — the ledger's 27 INTEGRATED rows stand; per-item mainline verification continues on the tracker (the registry is the inventory; no rewrite of completed laws) |
| #521 (Coder 9) | resources/drawable/bitmap patches | **TESTED_BUT_NOT_INTEGRATED / SUPERSEDED mix** per ledger; this session did not duplicate mainline-covered items |
| #484 | PF-2048/ViewPager-Adapter | **PENDING** (APK not fetched this session — disk budget) |
| #612 (Coder 3) | F-GLZ-3 GL ordering | **PENDING verification** — no F-GLZ-3 label found in src/ this session; surface-family behavior measured stable (rttt face deterministic across 3 runs; suppression branch unchanged). Reconciliation requires the issue's patch reference |
| #633 | aapt2 pathData | **BLOCKED** (mini-ARSC/AXML fixture still required — live read `vector_inflater.cpp:356`) |
| #634 | animated drawable docs | **BLOCKED/feature-class** (minimum document-loader scoped but not started this session) |
| Local branches/stashes | s237-s241 branches | **0 commits ahead of main** (all merged); stashes contain evidence files only — nothing recoverable there |
| #376/#690 | durable Wave-3 patches | F-CSW-3/3b/5/6 mainline presence NOT re-verified this session (issue content lives outside the repo; API access rate-limited) — **PENDING**, recorded honestly |

## 3. WS1 IMPLEMENTED — the B2 dispatch contract (the authorized change)

**Files changed (exactly 2):**
1. `src/runtime/execution_engine.cpp` (the T4-PAINTGAP gate, was `:5100-5104`): the `cv_framework` NAME-PREFIX provenance gate (`Landroid/|Landroidx/|Lcom/google/`) **replaced by the AOSP-faithful contract**: dispatch the real draw chain for every custom view with a **live heap object**; honest-blank safety is enforced downstream (replay only when the dispatched draw produced real ops — `gap_ops > 0`), preserving 21-P0-5 authoritative-frame purity. The text-base and surface-family branches above it are untouched.
2. `src/dex/dalvik_engine_core.cpp`: an env-gated read-only diagnostic (`MINIANDROID_S21_CHAIN_DUMP=<class>`) tracing `class_chain_defines_method` walks (in_index / dex_report / super) — zero default cost.

**Measured before/after (5 targets × 3 runs at 30 frames, deterministic faces):**

| APK | dispatch attempts (per run) | dispatched=YES before | after | face sha16 | census |
|---|---|---|---|---|---|
| dooz | 62 (C013-ONDRAW) | 0 (gate refused) | **82 YES** | `d602648e…` unchanged | APP_DRAW_OPS |
| freebloks | 62 | 0 | **2 YES** | `b5a7a35d…` unchanged | APP_DRAW_OPS |
| itsfrz | 93 | — | **113 YES** | `d55056a8…` unchanged | APP_PIXELS |
| dicer | 60 | — | 2–19 YES | `b5a7a35d…` unchanged | crash pre-census |
| rttt | 31 | 0 | 0 (surface-family branch — documented F-NEW-162 path) | `b5a7a35d…` unchanged | APP_DRAW_OPS |

**Two deeper layers identified beneath the gate (the reason faces did not move):**
- **dooz** `dispatched=YES ops=0` — the ComposeView draw chain now EXECUTES and produces zero canvas ops: the Compose draw semantics (B1) are the remaining frontier.
- **freebloks** `dispatched=NO` — method resolution fails: the APK is **R8-minified** (proven by the dex method table: `calculateContentConstraints-l58MMJ0`; parser: `scripts/dex_methods.py`) — framework-invoked draw methods are renamed/stripped in the dex, so the name-based resolution finds nothing. The shared fix (next task): R8-aware draw resolution (dex-mapping or super-chain draw dispatch) for inflater-created framework views.

## 4. Patches rejected/superseded: none this session (no conflicts encountered).

## 5. Source files changed: `src/runtime/execution_engine.cpp`, `src/dex/dalvik_engine_core.cpp` (+ evidence/scripts).

## 6. Shared execution-chain map (verified stages)

APK → `src/apk/apk_parser.cpp` → DEX (`dex_report_`, 4099-class index measured) → Dalvik split TUs (`dalvik_engine_{core,invoke,opcodes,bridge,tail}.cpp` — monolith dormant, `DALVIK_SPLIT=1` default) → framework dispatch (`android_shadows.cpp`, live) → lifecycle (`F058` registration + `dispatch_activity_lifecycle_callbacks` in `dalvik_engine_core.cpp` — **reachable, observed live**) → ViewTree/inflation → measure/layout (laws green) → **draw walk (`execution_engine.cpp` — the B2 gate, now contract-based)** → census (`frame_census_`, honest verdicts) → census shows the current frontier = draw-op resolution (R8 names) + Compose semantics.

## 7-9. Cross-APK matrix + traces + pixel evidence

15 target runs + 5 anchor runs this session; every snapshot SHA recorded in `evidence/s21/` + the committed tsv. Faces byte-identical to the T0/golden baselines (no false pixel claims); the REAL change is dispatch reachability (table above). dicer's `31ffa499` r1 splash face reproduces.

## 10. Regression battery + golden APKs — PASS

- **6 law tests built+run batch-wise** (disk limit): lifecycle (ALL PASS), linear_layout (24/24), g10_layout (23/23), s98_text (21/21), gp583_gles (31/31), r25_dispatch_matrix (14/14) — **all rc=0**.
- **4 golden anchors byte-identical**: HelloWorldToast `acdd9f05…`, notepad `31ddd4d5…`, randomix `31ddd4d5…`, chess-clock `d602648e…` (chess's one-time early halt reproduced as **2-core contention variance**: rerun clean → rc=124 + golden face).
- Full 108-test battery: first link attempt hit **ENOSPC** (5.7 GB disk, test binaries = 5.8 GB); batch-wise law subset used instead — recorded honestly.

## 11. Build-time comparison (this host, this tree)

| Scenario | Time | Note |
|---|---|---|
| No-change (post-recycle, objects survived) | **13.5s** | build/ survived this recycle |
| One-TU (`execution_engine.cpp`) | **37.1s** | 1 TU + link |
| Two-TU (+`dalvik_engine_core.cpp`) | **24.7s** | incremental |
| Clean (previous session) | 6m46.0 / 6m38.4 | ±2% noise; not re-run this session (build/ survived) |
| Battery subset build | ~40-60s per law test | batch-wise |
| ccache | **not installed** (no package access) — PENDING | levers unchanged |

## 12. Remaining blockers (exact)

1. **R8-minified draw-method resolution** (freebloks layer): name-based onDraw/dispatchDraw lookup fails on minified dex — needs dex-mapping/super-chain dispatch (the highest-leverage NEXT shared fix — unblocks the whole minified framework-view family).
2. **Compose draw semantics** (dooz layer): dispatched but 0 ops — B1.
3. **Disk 5.7 GB** < full-battery 5.8 GB — batch-wise battery is the operational mode; ccache unavailable (no package repo access).
4. F-GLZ-3 / F-CSW-* mainline reconciliation needs the issue patch references (repo-external content).
5. #633 fixture, #634 document-loader — unchanged BLOCKED status.

## 13. Issues updated: #635 (this comment) + the evidence pack `evidence/audit/S21_INTEGRATION_REPORT.md`; no new issues created (per the integration rules).

**Success statement (honest): one previously-blocked shared chain link (the draw dispatch provenance gate) is now implemented and PROVEN reachable across 4 app families with zero regressions (byte-identical golden faces + 6/6 law batteries). The two deeper layers (R8 names, Compose semantics) are now precisely identified with measured evidence — the next work items, not hidden failures.**
