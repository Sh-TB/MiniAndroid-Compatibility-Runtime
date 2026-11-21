# NEXT INTEGRATION PLAN — v2.1 (dependency-ordered; S14 state)
1. **MG-011 verification closure (AUD-55)** — fix applied + battery 49/49 (S12); a direct-vs-referenced
   PathData parity test (battery extension) remains the optional follow-up.
2. **#634 MG-012 re-implementation from the documented law** — animated-vector root acceptance,
   shared resolver-layer fix (`looks_like_entry` predicate), cycle depth-guard, AVD still-frame =
   referenced VD with own attributes; port the s257 V0-V4 law rows into TEST_LAW.
3. **#295/#296/#297 stroke laws** — cap/join/trim emitters with the right-normal sign law;
   extend s257 to strokeLineJoin/trimPath rows.
4. ~~**BUG-7 dedupe (AUD-49)**~~ DONE (S14): the stale copy was committed EMPTY and had ZERO
   includers — removed, battery 49/49 re-verified. No repointing was needed.
5. **CMake WEBP parity (AUD-07)** — add -DMINIANDROID_HAVE_WEBP to CMakeLists; proof = section
   compare vs the Make build (cmake now fully exercised: AUD-52 measured + RSS + ctest done).
6. ~~**#626 PR rebase**~~ RESOLVED-SUPERSEDED (S15/AUD-58): the wave10 line's entire content is in
   main via direct W22-W24 landings (13/13 F-NEW-7xx ids, 3/3 W20 P2 fixes, P0 split, dev-so
   profiles, ZERO missing src/tests paths) — no rebase, no cherry-pick; classification logged
   for the PR close decision. audit/s236 = superseded (test in TEST_LAW:531); m16-litehtml +
   cont24 = reachable branch-only experiments.
7. **RC-12 / layout apps** — only from the original coder environment; no substitutes.
   S15 re-verification: layout-geometry-001 absent from git ls-remote — still unrecoverable.
8. **AUD-54 focused tests** — S16 phase 1 (103/234 machine-checked) + S17 phase 2 (14
   inflater-decode laws) + S18 (131-row classification + 29 laws in 5 new families:
   rounding/weightSum/text-layout/sql-shadow/renderer-surface; 5-family negative-mutation
   validation; 11 more rows law-verified -> 114/234 HONEST, 120 classified remaining).
   S16 phase 1 detail:
   scripts/s16_cite_sweep.py (35 CONFIRMED-LIVE incl. verbatim line cites; 32 STALE-CITE-
   RELOCATED — the 25 old "ABSENT" marks corrected, the files exist relocated; 24 CITE-STALE;
   5 PARTIAL; 3 RESOLVED-IN-TREE: A1/BP-19/G3; 1 PATTERN-ABSENT). The S17 claim of
   114/234 double-counted 11 rows; the TRUE count reached 114/234 only in S18 (11
   more rows law-verified; the remaining 120 carry explicit S18 classifications,
   zero of which need the missing APKs or coder artifacts)
   are runtime-behavior claims needing focused laws (several depend on the missing APKs).
   S18-cont (2026-11-21): the D/E families are DONE — 8 laws over the LIVE inflater
   (gravity direction/fill + baseline/divider absence), 3 negative-mutation injections
   (one honest retarget recorded), battery 50/50; 5 registry rows upgraded ->
   118/234 settled, 116 classified remaining (AUD-60).
   S18-cont-2 (2026-11-21): family H (constraint anchors, 3 laws, mutation-validated)
   FALSIFIES B5 for the live path; A2-A8 census RE-MEASURED; B6-B9 dispositioned by the
   #635 audit's measured rejections/fixes; 11 more rows settled -> 129/234 settled,
   105 classified remaining (AUD-61).
   S19 (2026-11-21): the classified census queue is CLOSED — 92 rows settled by one
   self-measuring sweep (19 dormant rescopes via the Makefile's own DORMANT_SOURCES
   law, 30 census confirms, 8 law refutations incl. the grid margins-carry-the-gaps
   law, 10 partial refinements with counts, 22 plan acknowledgments) + family I 3/3
   with an honest retarget -> 227/234 settled, 7 rows remain (content-check class)
   (AUD-62).
8. ~~**UBSAN=1 profile (AUD-47)**~~ DONE (S14): `make UBSAN=1` (-fsanitize=undefined
   -fno-sanitize-recover=all, tree build_ubsan/); E-05 probes 7/7 + old-form abort rc=
   0 machine-reproduce the hub's claim; the FULL 49-test battery built and ran
   clean under the sanitizer (probes rc=0, battery 49/49 rc=0); w15 extended to 7 engine-tested const/high16 vectors.
9. **-Werror/CI (AUD-45)** — after the R1-R4 dead-code triage.
Standing rules: ABBA order for timing claims; evidence logs force-added; Production and Dev-So
reported separately; no semantic weakening for build speed; tracker closure is never runtime proof.
