**S16 — #632 cite re-sweep: 103/234 findings machine-checked (was 25); the 25 "ABSENT" marks corrected (ledger untouched at 64 rows, validator PASS)**

**1. Sweep (AUD-54 phase 1, commit to follow).** Every mechanically checkable claim in
632_FINDINGS.csv was re-verified against the CURRENT tree with `scripts/s16_cite_sweep.py`
(deterministic greps/wc/find; per-row verdict + detail now in the `source_check` column):

| verdict | count | highlights |
|---|---|---|
| CONFIRMED-LIVE | 35 | C3 + P1 confirmed **verbatim at the cited lines** (`android_shadows.cpp:11189` `measured_width = r - l;`, `:9785-9790` global `layout_dirty = true`) |
| STALE-CITE-RELOCATED | 32 | **the 25 old "cited X ABSENT" marks are corrected** — every one of those files exists under `src/resources/` or `src/renderer/`; the cites were stale paths, not missing code |
| CITE-STALE | 24 | cited line numbers belong to an older tree state; pattern status recorded per row |
| PARTIAL | 5 | e.g. BP-5: -g1 landed on the engine family, -g0 remains elsewhere; split DWARF still untried |
| RESOLVED-IN-TREE | 3 | A1 (build dirs untracked), BP-19 (battery behind -DBUILD_TESTS=ON), G3 (**Kahn topological sort now in layout_inflater.cpp:3223/3511** — forward-reference defect fixed) |
| PATH-AS-CITED-ABSENT | 3 | evidence fixtures (A4/N7/S10) not found even by basename |
| PATTERN-ABSENT | 1 | F2 `row_h = max(row_h, mb.h)` gone from both layout engines — fixed or rewritten |

**2. What this means.** Of the 190 LIVE registry rows, the build-pipeline family is now
settled: the monolith claim (BP-1, 94,305 lines) and no-cache claim (BP-3) are confirmed
still live; the "tests in default target" claim is resolved; G3's insertion-order defect is
fixed in the inflater. 131 rows remain NO-CITE — runtime-behavior claims (gravity tables,
dimension laws, font metrics, nine-patch, Robolectric oracle) that need focused laws and, in
several cases, the missing original APKs. That is the AUD-54 focused-test queue, now precisely
enumerated per row.

**3. Housekeeping.** The S15 recycle incident had also reverted `regen_deliverables.py` to its
S14 state; its S15 edits are re-applied and the regenerated deliverables reproduce the
committed v2.2 content plus the S16 additions (diff vs bb2964c2 = 4 files, S16-only).
Method + histogram: RAW_LOGS/s16_cite_sweep_2026-11-20.md. MASTER_AUDIT §1 item 14 added;
§4 updated (103/234); NEXT_INTEGRATION_PLAN item 8 records the remaining queue.

**Remaining open (unchanged):** coder-local artifacts (#634 MG-012, #295/#296/#297, RC-12,
#630/#631 — owner branch absent from remote); missing APKs (#597/#618/#623); AUD-10b/42;
PR #626 close decision (classification public, SUPERSEDED-IN-FULL).
