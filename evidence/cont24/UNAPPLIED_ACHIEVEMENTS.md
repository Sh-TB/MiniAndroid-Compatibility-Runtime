# UNAPPLIED ACHIEVEMENTS INVENTORY — scattered assets that never reached the main line

Date: 2026-10-09 · Source: `root_registry.json` @ 33fafcb9 + git history + wave reports.
Scope: work products that EXIST with evidence but are NOT active main-line behavior.
This is the user-directed census: "hours of work, roots found, various fixes —
applied nowhere, scattered, unused. Find them."

## 1. Registry classes (586 roots scanned)

| class | count | meaning |
|---|---|---|
| RESEARCHED-NOT-IMPLEMENTED | **16** | researched with evidence, never landed |
| PARTIAL | **110** | half-landed: some sites fixed, frontier open |
| UNPROVEN | 72 | registered suspects, proof work never done |
| CLASSIFIED / OPEN / OBSERVED-FAIL | 6 / 4 / 5 | live queue (15 total) |
| SUPERSEDED-BY-EVIDENCE | 12 | kept for history |
| NOT-APPLICABLE | 42 | honest dead rows |

### 1a. RESEARCHED-NOT-IMPLEMENTED — the 16 fully-unapplied rows

- R-NEW-047/048/049, R-NEW-114..121 (12 rows): **jni_bridge.h boundary
  classification** — the law "a missing .so is NEVER a Java-API blocker" was
  researched and classified but no classification machinery landed.
- R-NEW-050: ART-specific interpreter binding (N/A as-is, no port made).
- R-NEW-064: ZIP entry semantics + .so selection (evidence only).
- R-NEW-164/165/166: **tooling class G + differential harness (planned,
  PHASE-0 infra)** — harness designs with zero implementation.

### 1b. PARTIAL — largest clusters (110 rows; examples)

- R-NEW-021 ViewShadow measure/layout pipeline (G04/G06) — the exact area the
  CONT-24 skel-light experiment measured from the other side.
- R-NEW-004/005/006 locks_shadow F-017 family (3 rows).
- R-NEW-015/017 reflection core F-029.
- R-NEW-020 Bundle heap store (Intent extras), R-NEW-024 MeasureSpec
  EXACTLY/AT_MOST, R-NEW-031 ARSC drawable resolver, R-NEW-034 density
  approximation — each has runtime evidence of the part that works.

## 2. Git-history assets (code that existed, proved something, and is NOT in main)

| asset | size | status | evidence |
|---|---|---|---|
| CONT-23 falsified lifecycle-transaction DEX patch | engine patch | REVERTED (double-dispatch disproven by its own probe) | worklog CONT-23; probe locked 5/5: `fixtures/lifecycle_transaction_probe` |
| CONT-12 real-Compose oracle (oracle12.apk: 55-artifact Maven set, real Kotlin probe) | full APK | TEST-ONLY by design — advanced past R8-masked walls, proved F-NEW-266; never shipped | commit f0a36646 |
| dead experiment chain: dex_interpreter v2 + exp018/exp019 chains + orphan mains | 10,258 LOC | DELETED as unreferenced (f9f3013d) — achievements preserved only in history | commit f9f3013d |
| view_renderer.cpp (UNIFIED_007 measure/layout + draw module) | 684 LOC | **STALE — does not compile against current ViewShadow API** (padding_l/text_style_bold/TextShaper drift; found during CONT-24) | src/renderer/view_renderer.cpp |
| EXP-088-era pixel-block renderer, EXP-087 | engine block | superseded in-tree by the draw walk | execution_engine.cpp history |

## 3. Fixture-locked laws (proven, env-gated, invisible by default)

- `fixtures/lifecycle_transaction_probe` — API-29 start/resume transaction
  pairing assertion, 5/5 PASS at the unmodified binary; locks the G09 law for
  the next wave's F-NEW-277 fix.
- `MINIANDROID_SKELETON_LIGHT=1` (CONT-24, this wave) — structure-frame
  instrument, default OFF, branch `cont24/skeleton-light-experiment`.

## 4. Recommended next actions (priority order)

1. **view_renderer.cpp**: either delete (it is dead, 684 LOC) or repair to
   become the shared measure pass — keeping a non-compiling "renderer" in-tree
   is exactly the scattered-asset pattern the user flagged.
2. **jni_bridge classification law** (12 R-NEW rows): one generic law could
   close 12 rows at once — highest single-law ROI in the unapplied set.
3. **PARTIAL harvest**: the 110 PARTIAL rows each carry a "what works" note;
   a sweep that re-verifies each at current HEAD would either promote or
   honestly close them (registry hygiene + real capability recovery).
4. Keep the skel-light instrument env-gated for corpus smoke-testing; do NOT
   let its verdict class leak into REAL_APP_CONTENT claims (see §5 of
   SKEL_LIGHT_EXPERIMENT.md).
