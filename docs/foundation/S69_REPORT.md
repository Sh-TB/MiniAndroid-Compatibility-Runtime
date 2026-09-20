# S69 REPORT — FINAL FOUNDATION / SOURCE-LINKED RUNTIME CAMPAIGN

Runtime head at start: **8c917d41** (S68-W2). Campaign brief: the 25-section
FINAL FOUNDATION / SOURCE-LINKED RUNTIME directive (§0–§25).

## 1. What this campaign changed

MiniAndroid can now answer, with one query, every §23 question for the corpus:
which Android contract an app consumes (dex_census), which subsystem serves it
(api_matrix + served_api), whether that contract was already tested (fixtures
+ battery + live status), which source file the app's class comes from
(source_map with pinned commits), which failure was already recorded
(failure_index), and how it ends in pixels (live_runs per-frame evidence).

## 2. RECON (§24 first step, zero code changes)

- git: HEAD 8c917d41, tree clean, **6 commits ahead of origin (push debt ×6,
  no credential in session)** — recorded honestly, no fake push.
- toolchain re-bootstrapped (aapt2/ecj/r8/android-34.jar), engine rebuilt,
  androguard installed; zoekt/go still absent (container reset, ledger note).
- baseline re-validated before any change: fixtures 21/21, battery 92/94
  (EXT-01/02 environmental), canonical corpus recipes from the S65 ledger.

## 3. Deliverables produced (all machine-readable, §20/§21)

| deliverable | file | content |
|---|---|---|
| class graph | docs/foundation/graph/class_graph.json | 387 classes, inheritance, headers |
| API graph (static) | graph/served_api.json | (class,method) dispatch guards per TU (over-approx flagged) |
| subsystem graphs | graph/subsystem_graphs.json | render/lifecycle/input/resource/runtime function-call chains |
| DEX census | dex_census/<pkg>.json + _aggregate.json | 11 APKs: 3674 distinct APIs, 213,251 call sites, per-API fan-out |
| live dispatch surface | live_runs.json (+ run/s69_live/*/api_calls.json) | 10 APK runs, per-call IMPLEMENTED/STUBBED/MISSING, per-frame nonwhite + SHA |
| API coverage matrix | api_matrix.json | status law: LIVE-IMPL 163 / LIVE-PARTIAL 1 / LIVE-STUB 68 / UNSERVED 3442 (mostly Ljava interpreter-intrinsics) |
| source↔runtime map | source_map.json | 9 repos pinned (10/11 APKs; uNote honest UNPINNED), source↔DEX 1:1 for non-obfuscated apps |
| failure index | failure_index.json | 372 roots, statuses preserved, nulls = not recorded |
| runtime graph | runtime_graph.json | the §21 aggregator |
| canonical map | docs/FOUNDATION_RUNTIME_MAP.md | the chain with per-hop implementation/index/gaps |
| tooling | tools/architecture/ (5 generators + README) | permanent, regenerable |

## 4. Fix wave — F-135 (the full §17 cycle)

Fan-out first (§14): the census ranked `Double/Float .isNaN/.isInfinite/
.compare` at **694 static call sites × 7 APKs** with the live trace showing
**480× STUBBED** in bouncy alone — every NaN-guard branch silently wrong.

- CONTRACT: OpenJDK Double.java:1031 `(v != v)`, :1048 `abs(v) > MAX_VALUE`,
  :1538 canonical-bits ordering (NaN > +Inf, −0.0 < +0.0); Float.java:631 —
  fetched to docs/upstream/openjdk/ (SHAs in SEARCH_LEDGER S69)
- ROOT CAUSE: bridge fell through to a stub answering false/0
- IMPLEMENTATION: dalvik_engine.cpp F-135 block — generic java.lang law
- MICRO FIXTURE: f52_nanlaw (9 rows; NaN/±Inf PRODUCED via IEEE div, not
  hard-coded) — 9/9 exact pixel rows; registered in verify_foundation.py
- REAL APK: bouncy NaN-family flips 480× STUB→IMPL; frames byte-stable
- DETERMINISM: f52 ×3 byte-identical (b9d4fdb3…)
- REGRESSION: 22/22 fixtures · battery 92/94 (EXT-01/02 only) · canonical
  corpus frames byte-identical (fishrings frame_004 = 2,072,211 px reproduced)

Runtime capability added: `--dump-api-trace` (S67 `--dump-view-tree` pattern).

## 5. Source-linked findings (SOURCE PROGRAMS AS ORACLES, §15)

- fishrings: 6/6 source classes map 1:1 into the DEX; the S65 S10 chain
  reproduces exactly under the S69 re-run (2072211 → … → 7,347 px diff chain
  recipe re-recorded in live_runs).
- tripeaks: 14/14 mapped; R-NEW-388 geometry gap re-confirmed by source
  (alignParentLeft/Top + margins idiom) AND by pixels (205,638 px board at
  wrong positions) — the gap now has source + DEX + pixel + live-trace
  provenance in one record.
- dooz: R8-obfuscated — 2/68 source files resolvable; recorded UNMAPPED
  (honest), Compose campaign stays separate (§19).

## 6. Honest failure accounting (§22)

- LIVE-STUB tail: 68 distinct APIs observed answering stubs (per-APK list in
  live_runs.json; API matrix rows LIVE-STUB).
- UNSERVED android.* high-fan-out (static): Trace.beginSection/endSection
  (dooz ×106+286 sites — Compose tracing no-ops), Context.getString ×130,
  getSystemService ×84, Rect.<init> ×82 — queued by fan-out, laws to mine.
  (Static extraction under-approximates the served surface; live status wins
  wherever both exist — the matrix encodes that precedence.)
- Remaining P0s unchanged: R-NEW-388 (RL geometry wiring), A7 (manifest
  label/icon) — both pre-registered with law + plan.
- Push debt: ×6 commits (S67/S68) + this session = 7 after commit. NO
  credential in session env — PENDING-PUSH recorded, no fake push.
- uNote source UNPINNED (gitlab 403 all session) — commit identified
  (4165c80d), re-fetch queued.

## 7. FOUNDATION COMPLETE? — NO (and where the frontier is)

The campaign's exit gate (§20) is not met while R-NEW-388 and A7 remain and
the LIVE-STUB tail is unmapped to laws. What IS new: every gap is queryable
with fan-out × consumer evidence attached, 10/11 APKs are pinned to upstream
commits, the corpus census is regenerable in one command, and the highest
fan-out silent-wrongness family found this session (NaN/compare) is
implemented, pixel-proven, deterministic, and regression-clean.

## 8. Next waves (priority = fan-out × semantic weight × consumers)

1. R-NEW-388: renderer consumes RL-solved geometry (TriPeaks consumer, P0,
   law already mined from source).
2. A7: manifest label/icon through ARSC (corpus-wide).
3. LIVE-STUB tail by fan-out: Trace.begin/end (no-op-with-count law),
   Context.getString (ARSC law exists — route it), Rect.<init> (object-model
   law), EditText.getText.
4. uNote pin completion + dooz Compose LayoutNode campaign (§19, separate).
