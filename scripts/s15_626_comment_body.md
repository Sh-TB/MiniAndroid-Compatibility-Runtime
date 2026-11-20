**Audit classification (S15/AUD-58, cross-ref [#635](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/635#issuecomment-7045210802)): the content of this PR is now fully in main — SUPERSEDED-IN-FULL.**

This PR's head (`wave10/dalvik-accel` = `671d2577`) carries 15 commits stacked on merged wave9
(PR #625). A per-piece content census against main today (full evidence:
`evidence/audit/RAW_LOGS/s15_branch_classification_2026-11-20.md` on `main`):

- **All 13 F-NEW-7xx ids** (709–723b) are present in main `src/` — including the F-NEW-710
  declaring-class **by-value** fix verbatim at `dalvik_engine_invoke.cpp:187-191`.
- **W20 P2's three fixes** are in main: `<cstdint>` in `adapter_scrap_bin.h`, the unnecessary
  `android_shadows.h` include removed from `dalvik_engine_tail.cpp` (0 refs / 599 lines), and
  the dev-so `.d` dependency `-include` block at `Makefile:817-820`.
- The **P0 split** and **dev-so profiles** exist in main in a further-evolved form (domain TUs
  refined by W22-C/W23 measurements; `docs/dev-so-architecture.md`).
- **Zero src/tests paths** touched by this branch are missing from main (`git cat-file -e`
  loop → 0 MISSING-IN-MAIN); the remaining branch-only delta is `scripts/` + `evidence/`
  working artifacts.
- Law tests: f709/f714/f716 files + the F-NEW rows in `input_pipeline_law_test.cpp` are in
  main's battery (49/49 PASS as of 2026-11-20).

**Recommendation: close this PR** — merging/rebasing would resurrect duplicate implementations
against main's further-evolved architecture. The branch stays on the remote as the original
coder history (nothing deleted). This classification was produced by the cross-coder audit; the
close action itself is the owner's call.
