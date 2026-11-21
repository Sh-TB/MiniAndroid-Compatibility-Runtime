**S20 — the #632 registry audit is COMPLETE: 234/234 settled. #633/#634 assessed at code level.**

Branch restored after a fourth sandbox rewind (hard reset to `1888f11d`). Fresh issue fetch (#635 + all 11 comments, #633, #634 — `RAW_LOGS/s20_issues_2026-11-21.md`) confirmed **no new external directives** — the two morning comments are this audit's own S18-cont/cont-2 posts.

**1. The last 7 rows content-checked AT CODE LEVEL** (`scripts/s20_content_checks.py`, log `RAW_LOGS/s20_content_checks_2026-11-21.log`, per-row uniqueness pre-flight) — every verdict carries an exact code site:
- **NEW-2 REFUTED** — the live weight re-measure (`layout_inflater.cpp:3985-4045`) contains no tautology: every comparison is load-bearing; the share math is pinned by the weightsum law family + MASTER-2 FIX-MEASURE-003 (:4457-4460).
- **NEW-12 REFUTED** — scaleType in the live draw path IS law-verified: the s246 battery's scaleType-geometry group + `c48773a0` ("scaleType raster proven at AOSP parity") + the live enum decode (`android_shadows.cpp:10330-10352`) + the full 8-case scale law (`software_renderer.cpp:425-470`).
- **NEW-14 RESOLVED** — CENTER/CENTER_CROP rects exceed the box **by design** (that IS the AOSP crop law, verbatim); clipping exists as the S68 canvas-clip law (`SoftwareCanvas::set_clip`/`clip_allows` :157-169, per-pixel gate :213); the verification the row asked for was done by c48773a0's raster parity — no defect remains.
- **NEW-24 REFINED** — the ad-hoc `size*1.2` heuristic was **replaced** by the G36 face-derived FontMetrics law (`text_shaper.cpp:840`, `text_shaper.h:117-180`, in-battery); the engine's Paint shadow keeps documented em-fraction constants (:53597/:54032) — not a heuristic fallback.
- **NEW-26 CONFIRMED** — the residual is REAL and located: `text_shaper.cpp:619` allocates `vis(src.size() + 1)` while log2vis fills only `src.size()` (the in-code comment :629 documents it). One element per shaped string — bounded, non-corrupting; the phantom-NUL feed fix itself is correct (:636/:683 exactly `src.size()`). Fix = plan item.
- **NEW-28 REFUTED-as-defect** — the qualifier string is a one-way human-readable description (`res_config.h:123`); resource matching uses the structured `ResTable_config` fields (the best-config law `arsc_parser.cpp:644-666` + isBetterThan :348-353) — a lossy description cannot corrupt selection.
- **NEW-32 REFUTED** — the density-scale arithmetic is ONE pure law (`bitmap_factory_density_law`, wrapper :257-268, applied :373) fed by the SHARED `device_config()`; the measure side uses the same config for the DISTINCT isBetterThan bucket law (:2841/:348-353) — distinct laws over one config, not duplicated arithmetic.

No new behavior claims → no new laws needed; the behavior evidence already lives in the battery (s246 + c48773a0). **Queue: 131 → 0. 234/234 settled honestly.**

**2. #633/#634 assessed AT CODE LEVEL** (`TRACK_A_ISSUE_DIGEST.md` S20 section):
- **#633 [MG-009]** — the live pathData read is `vector_inflater.cpp:356`; the ARSC string-pool indirection is resolvable (the inflater holds the arsc), but the law test needs a hand-built **mini-ARSC/AXML fixture** — the same fixture class as N2/P8/N8. MG-011 (fail-honesty, `vector_decode.cpp:942`) is already in. Verdict: implementable-with-fixture — **BLOCKED at the mini-ARSC fixture**.
- **#634 [MG-012]** — confirmed at code level: the live inflater has **no animated-vector branch**, the dormant copy explicitly rejects it (`vector_decode.cpp:495-497`), and **no drawable-document loader exists** (grep = 0). The fix is a new subsystem (drawable-doc loader + ref resolution + wire-in), not a patch. Verdict: **feature-class**.

**3. Ledger +AUD-63** (SOURCE-INSPECTED, 69 rows) — the first append used the non-canonical level `MEASURED`, caught by the validator, corrected → **OVERALL PASS**. Deliverables regenerated **v2.5** (item 20, 69-row arithmetic, §4 complete-registry sentence, BLOCKED row, PLAN item 8).

Next queue: the NEW-fixture rows (N2 font, P8 mini-DEX, N8 image — the mini-ARSC fixture also unblocks #633), then #634 feature-class. Registry watch continues on fresh claims.
