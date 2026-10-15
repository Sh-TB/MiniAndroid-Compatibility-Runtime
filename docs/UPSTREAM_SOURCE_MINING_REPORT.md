# UPSTREAM SOURCE MINING REPORT — CONT-71 (living document)

Status: **PARTIAL — wave 1 of the #364 master mining card (comment 6201160604).**
This report and `docs/UPSTREAM_SOURCE_MINING.jsonl` are the living deliverables;
each CONT wave extends them. The card's full quota (30–50 audited candidates)
is NOT yet met — the count and the audit depth grow wave by wave, honestly.

## Executive summary (wave 1)

Wave CONT-71 executed the #364 loop end-to-end on ONE foundational area —
**the exception-delivery + view-measure primitive family** — and produced:

1. **First-divergence decodes backed by fetched upstream source.** The androidx
   `CoordinatorLayout.java` (androidx-main mirror, 148,913 bytes) was fetched
   and read at source; its `onMeasure` ends with
   `setMeasuredDimension(View.resolveSizeAndState(...))` and delegates child
   negotiation to the inherited `ViewGroup.measureChildWithMargins`. The engine
   had NO shadow for either primitive — every real DEX container `onMeasure`
   silently lost its child negotiation and its answer law.
2. **Laws implemented (AOSP-verbatim), shipped env-gated OFF.**
   `MINIANDROID_F368_LAW` (exception subtype-table extension: reflective +
   java.net + concurrent + android families, OpenJDK/AOSP documented parents),
   `MINIANDROID_MCM_LAW` (`ViewGroup.measureChildWithMargins` negotiation +
   `View.resolveSizeAndState`/`resolveSize`/`getMeasuredState`/
   `combineMeasuredStates` answer family, with ViewRootImpl spec-bounds gates).
3. **Activation proof + honest blocker.** Under the activated pair the memory
   app renders its exact record face (`c559b630dd8f0f0f`) with the delivery
   row `deferred handler @0x53 type=Ljava/lang/Exception;` and the app's own
   catch log line — the F-NEW-368 delivery works. The SAME activation
   deterministically diverges opencalculator v53 (`3e73a5ad`, collapsed): the
   SlidingUpPanelLayout DEX `onMeasure` (R-NEW-441 family) is incompletely
   emulated and its read-back of newly-measured children produces in-bounds
   but wrong specs. The per-container DEX-measure trust law is registered as
   **F-NEW-374 (P1)** — the named next lever.
4. **Zero drift at the default binary** `86e4ebd4a2c30592`: wall 13 rows x 3 =
   39/39 MATCH (incl. the repaired microtimer row — the pushed
   `cont70_gate.sh` microtimer line was an invalid bash identifier and
   silently skipped the row since batch 1; disclosed), gate-A probe ALL PASS,
   negatives 19/19, reinstall 8/8, goldens 4/4, skill 13/13, TSP 14/14 rows
   byte-identical, LLK 56/56 byte-identical, validator PASS, cold memory
   `3a3ba873` and warm `c559b630` records intact.

## Search methodology (this wave)

- Source-first: the failing symbol chain (`CoordinatorLayout.onMeasure` ->
  `measureChildWithMargins` -> `resolveSizeAndState`) was read at the upstream
  source before any patch; the android.googlesource/androidx mirrors were
  reached through the GitHub API.
- Trace-first locally: opt-in spec-plumbing traces (`MINIANDROID_M71_TRACE`)
  exposed the exact (view, spec) chain; the R-NEW-438/R347/M71 rows pinned the
  first divergence to the two missing shadows.
- Negative control: the spec-bounds gates (ViewRootImpl monotone-derivation
  law) decline specs no real pass can produce — verified against the opencalc
  garbage-spec decode (`EXACTLY(1073740479)`).

## Ranked shortlist (wave 1 rows — see the JSONL for the full records)

| id | candidate | category | disposition |
|----|-----------|----------|-------------|
| U-01 | OpenJDK ReflectiveOperationException family | SEMANTIC_REFERENCE | ADAPTED (table rows) |
| U-02 | ART exception.cc catch-walk | SEMANTIC_REFERENCE | contract matched |
| U-03 | ViewRootImpl spec derivation | SEMANTIC_REFERENCE | ADAPTED (bounds gates) |
| U-04 | androidx CoordinatorLayout.java | SEMANTIC_REFERENCE | FILE FETCHED, laws implemented |
| U-05 | ViewGroup.java measureChildWithMargins | SEMANTIC_REFERENCE | ADAPTED (shadow) |
| U-06 | View.java resolve family | SEMANTIC_REFERENCE | ADAPTED (shadow family) |
| U-07 | androidx ViewPager.onMeasure | SEMANTIC_REFERENCE | PENDING (F-NEW-374 target) |

## Honest limitations

- 7 of the required 30–50 audited candidates are recorded; the seed list
  (#364 comment 6201160604, 68 leads) remains the pool for later waves.
- Only U-04 was a full-file fetch this wave; U-01/02/03/05/06 are
  contract-level audits (implemented from documented AOSP/OpenJDK contracts)
  and are marked as such in the JSONL.
- The CONT-71 laws are NOT active by default: the per-container trust lever
  (F-NEW-374) must land first; the default binary is byte-equivalent to the
  previous wave (wall-proven).
