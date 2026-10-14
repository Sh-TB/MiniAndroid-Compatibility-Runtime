# CONT-16 — RECONCILIATION + FIX-BATCH EVIDENCE

Date: 2026-10-07 · Base HEAD: 80a340ab (CONT-15 WAVE 9) · Fix-batch binary: `a8761a482a186eac`
Directive: user request "pick the remaining ~50, make each a small task, solve many small
problems instead of one big one" — reconciled against GitHub issues #375/#379/#380 (HTML
lineage fetch, API rate-limited), the 575-row registry, and the CONT-15 frontier.

## 1. GitHub lineage consumption (PHASE 0)

- `evidence/cont16/github_issues.json` — full HTML-extracted bodies:
  - #379 (CONT-9 W5 directive): F-NEW-256 continuation discipline, KB searchlight rules,
    six-game claim, no-fallback law. Status: consumed by CONT-9..12; F-NEW-256 superseded
    by F-NEW-265 (CONT-11 re-root); six-game claim re-validated 6/6 x3 at CONT-15.
  - #380 (CONT-11 W7 directive): Kotlin reuse matrix, F-259/259b genericity audit, collection
    coverage matrix, AndroidCanvas first divergence. Status: consumed; F-NEW-264d audit
    (15/18 rows → 6 laws) is the surviving bounded queue.
  - #375 (BASE follow-through): §3 known partials — R-NEW-464 (CLOSED, registry row now
    ROOT-CAUSED-FIXED), ViewPager mCurItem (APK identity gate), F-NEW-221 (R8 merged-class),
    Fragment host separation, F-NEW-084 interpreter-halt cap. All carried into the CONT-16
    backlog (T-21..T-24) rather than re-declared.
- Issue comment threads: none renderable without login (comment bodies absent from the
  public HTML); issue bodies were the ledger source. Recorded as NOT FOUND IN COMMENTS.

## 2. Fix batch (this wave) — one law = one generic fix

| Root | Law | Fix site | Probe proof |
|---|---|---|---|
| F-NEW-266a | ART null-receiver NPE before any callee body (two layers: Dalvik untyped-register null `const/4 0`; default-method route gate before memo) | `f141_is_null_receiver` INT32-0 arm (dalvik_engine.h) + `try_interface_default_invoke` gate (dalvik_engine.cpp:5679) | f266 row D flipped: NPE=true, r4=0 → **6/6 PASS** |
| F-NEW-259g-a | OpenJDK ArrayList/LinkedList get range law (`IndexOutOfBoundsException`, "Index: N, Size: S") + generic SHADOW EXCEPTION CHANNEL | CallResult exception kind (shadow_registry.h/.cpp) + 3 conversion sites in try_shadow_dispatch + CollectionShadow get bounds block | f259g row K flipped: n=2 k1,k2 (was n=4) → **12/13** |
| F-NEW-259g-b | java.util.Vector materialization/iterator NPE (registered finding) | `Ljava/util/Vector;` claimed by CollectionShadow → generic F-237 iterator box over the F-NEW-246 array store | f259g row L: NPE GONE, JDK-honest zero iteration; row-L ISE expectation classified PROBE ARTIFACT (contradicts F-068 most-derived dispatch — the DEX body of NoSlots.iterator() must run; real Android behaves identically) |

No app-specific code, no R8-name knowledge, no suppression, no budget change.

## 3. Regression battery at `a8761a482a186eac` — ALL GREEN

- Anchors **6/6 ×3 byte-identical** (SCALED UP from the 5/5 set): dooz `d602648e8e401895`,
  microtimer `da73010a37dd0189`, unote `4f1a9e4e8f64fae8`, gmdice `f3b483fe7b7cf51b`,
  opencalc `a976d2f9fb675cb3`, chess `b5a7a35d5fe0564b` (jwtc.android.chess package
  corrected from the stale jp.sblo row during the run).
- f259 probe **7/7**; f259g **12/13** (K fixed, L honest); f266 **6/6** (D fixed);
  fcol audit **3/18** — UNCHANGED vs the recorded state (K7/K8/K10 PASS; the 15 FAILs are
  the F-NEW-264d six-law queue) → zero regression from the exception channel + range law.
- Negatives **19/19** (`s41_gatea_negative.py`); Skill selftest **13/13**.
- Pre-fix probe state preserved at `run/cont16_prefix/probe_report.json`
  (f266 5/6, f259g 11/13 — exactly the registered rows), post-fix at
  `run/cont16_postfix2/probe_report.json`.

## 4. Registry delta

- F-NEW-266a CLASSIFIED → **ROOT-CAUSED-FIXED**; F-NEW-259g-a REGISTERED → **ROOT-CAUSED-FIXED**;
  F-NEW-259g-b REGISTERED → **ROOT-CAUSED-FIXED** (with the probe-artifact note).
- Open rows 235 → 231; `status_counts` refreshed; F-NEW-264d re-verified UNCHANGED (still
  REGISTERED, 15 rows in 6 laws).
- Binary-SHA lineage note: 0ee46f5a719d2a8c (CONT-15) → a8761a482a186eac (CONT-16 fix
  batch); anchors prove semantic identity across the change.

## 5. What this wave deliberately did NOT do

- No F-NEW-264d law implementations (each is a bounded future fix with its own probe gate).
- No F-NEW-265 patch (the P0 Compose measure-death root stays single-highest-ROI; its
  three arms are decomposed into T-01..T-03 of the backlog).
- No bulk-status flips without fresh runtime evidence (the stale-P0 reconciliation tasks
  T-31..T-38 remain scheduled — each needs a live run at HEAD before its status moves).
