# PRESERVED WORK MANIFEST — v2 (nothing disappears)

## Integrated in mainline (verified)
- W22-W24 build architecture chain (FASTPROFILE, -g1, W24TIERS tiering, ABBA discipline,
  steal root-cause): commits 29a708c3 -> 4ada9e3e -> 68f4fe58 -> cfd0870e -> d8b8fbb9.
- Wave-7 interpreter contract + wave-10 PIC profiles (make -n matrix, cfd0870e).
- BUG-1/1b OBJECT libs, BUG-4 battery env, BUG-5 placebo law, BUG-8 parse-order fix.
- P0 architectural split of dalvik_bridge.cpp (55,995 -> 748-line coordinator + 5 domain TUs,
  screenshot gate 11/11 IDENTICAL, commit 8e225b25 line) — content reached main; the wave10
  branch keeps the 15-commit raw lineage.
- S236-S240 coder waves (s241-law-waves, s237/s238/s239/s240 branches): ALL MERGED into main
  (merge-base == tip) — F-NEW-639 bounded append (the '777' fix, #597's root cause), regionMatches
  port, generic-law battery, corpus lane, six-pin gate runner, #606 LAYOUT-PIPE-001 laws
  (s246, 47 laws incl. scaleType geometry + RelativeLayout center fix + HSV width law).
- MG-011 ok-fix (#633) — APPLIED THIS SESSION (vector_decode.cpp:942), build+battery verified.
- BUG-7 dedupe (AUD-49, S14) — stale EMPTY src/dex/shadow_registry.h removed; battery 49/49 after.
- UBSAN=1 profile + E-05 probes + 7-vector w15 const/high16 rows (AUD-47, S14) — INTEGRATED.
- .DELETE_ON_ERROR (AUD-09), AUD-51 untrack+gitignore (051af519).

## Confirmed to exist but NOT in mainline (recovery list)
- RC-12 ScaleType oracle + probe + 4 commits (46ca6258/73dcadb6/1439627a/d77edba6): coder-local
  branch `layout-geometry-001` (per #631 comments); UNRECOVERABLE from every source checked here;
  capability partially superseded by c48773a0 + 7e5473be.
- #631 LAYOUT-GEOMETRY-001 ten diagnostic apps: built by the coder (comments 7021630435/7021652138
  carry visual evidence), coder-local only; no substitutes may be generated (mission rule).
- #634 MG-012 (AVD still-frame law + resolver-layer fix + cycle guard + s257 V0-V4 tests):
  coder-local implementation, documented in the issue body; NOT re-implemented here.
- #295/#296/#297 stroke laws (cap/join/trim, s257 family): coder-local, same status.
- audit/m16-litehtml: vendored litehtml prototype behind MINIANDROID_USE_LITEHTML (OFF default),
  probe binary + pixel-hash receipts; parity-optional by design, never linked into the engine.
- cont24/skeleton-light-experiment: measured branch-only experiment (hazards documented);
  preserved as REJECTED-EXPERIMENT, unapplied by design.
- wave10/dalvik-accel: 15 commits (W16-W20: dev-so dep-graph fix, corrected bottleneck theory,
  PCH rejection with data, additive dev targets) — raw lineage preserved on the branch.

## Preserved rejection record (REJECTED_AND_CORRECTED.md)
mold/lld, -gsplit-dwarf, ggc-min tuning, -fno-var-tracking, Ninja, PCH x3, inline-budget placebo,
job pools at -j2, RC-12-exact-commits (unrecoverable), B2's "52 links" for the DEFAULT cmake graph.

## Stashes (preserved, not dropped)
- stash@{0} wave10/dalvik-accel "auto-checkout-recovery": 62 files, +12,352 lines (w20 corpus
  census + traces). stash@{1}: empty diff (recovery stub).
