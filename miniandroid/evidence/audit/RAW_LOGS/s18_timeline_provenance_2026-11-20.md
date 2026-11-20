# S18 timeline provenance — repository state reconciliation (2026-11-20)

This note records the S18-1 baseline verification against the repository
state as actually found, per the mission's own rule ("Do not assume the
reported commits are still HEAD. Verify remote main, working tree, and
current evidence first.") — including the reconciliation of a stale local
clone against the live remote.

## What was found

1. **The local clone was STALE**: its HEAD sat on the W23 line
   (c82992d3 → 2580a504 → 3dbbf9c4 → d7fe7c6c) and it had no knowledge of the
   audit commits. At first fetch the stale tracking ref also answered
   origin/main = d7fe7c6c.
2. **The working tree carried the complete audit state as untracked files**:
   `evidence/audit/` (11 deliverables + the S16/S17/S18 RAW_LOGS), the
   classified `632_FINDINGS.csv` (103 S16-CHECK + 11 S17-LAW + 131 S18-CLASS
   + 11 S18-LAW marks), the 65-row `ACHIEVEMENT_LEDGER.csv` (validator
   OVERALL: PASS), `tests/s17_focus_laws_test.cpp` + five `tests/s18_*.cpp`
   law files, and completed-but-uncommitted production changes
   (MG-011 ok-fix, inflate_element private→public, AUD-47 E-05 vectors,
   AUD-51 gitignore, W23-P120 Makefile profile).
3. **The live remote, once fetched properly, already contains the full audit
   timeline**: d7fe7c6c → ffbecca7 (S16) → b53627d0 (S17) → 3f9a3f6c →
   ed7df15f (S18) → 3c6007b7 → 1f1b1c7f — i.e. the S16 cite-sweep, S17 laws,
   and S18 classification commits all exist upstream, together with the
   W23-P120 evidence, the MG-011 fix, the inflate_element move, and the
   AUD-51/AUD-09 housekeeping (Makefile FASTPROFILE + .DELETE_ON_ERROR
   verified present in origin/main:miniandroid/Makefile).
4. **Byte-identity verification**: every tracked-modified or untracked file
   that appeared "pending" in the stale clone was compared against
   origin/main with content diffs — `.gitignore`, `Makefile`,
   `dalvik_engine.h`, `vector_decode.cpp`, `layout_inflater.h`,
   `w15_dalvik_lit_from16_law_test.cpp`, `W23_BUILD_RESULTS.csv`,
   `W23_FINAL_MISSION_REPORT.md`, `build_bench.jsonl`,
   `632_FINDINGS.csv`, `ACHIEVEMENT_LEDGER.csv`,
   `LEDGER_VALIDATION_REPORT.md`, `s18_weightsum_laws_test.cpp`,
   `s17_focus_laws_test.cpp` — ALL byte-identical. The untracked
   `evidence/w24/`, w22 E-05 probes, and w23/w24 session scripts are likewise
   already tracked upstream.

## Reconciliation performed

- The one local commit made on top of the stale line (016391b6, carrying only
  content verified byte-identical upstream) was discarded via
  `git reset --hard origin/main`; nothing was lost (identity proven above).
- Exactly three genuinely new artifacts from the fresh-verification session
  are committed by the follow-up commit:
  1. `RAW_LOGS/s18_freshrun_2026-11-20.log` — the complete fresh rebuild +
     regression on the recycled sandbox: full -j2 rebuild 8m36s, ENOSPC
     during the first attempt (a stale 6.1G `/tmp/my-project` copy verified
     byte-duplicate and deleted, then the two regenerable untracked scratch
     trees `build_p2b` + `build_fast` removed per the S17 precedent — sizes
     archived in the log; `build_w24_cand_a` AUD-51 evidence untouched), then
     s17 14/14, all five S18 families green, spot-check negative mutation
     (family A floor removal → A2/A3 FAIL 5/2 rc=1 → reverted → 7/7), and
     BATTERY SUMMARY total=48 passed=48 failed=0 rc=0.
  2. This note.
  3. `scripts/s18_check_comments.py` — the #635 comment dedupe checker.
- The #635 evidence comments (7047192228 S16, 7047804487 S17, 7050053269 S18)
  reference commits that ARE reachable in the live remote history — the
  "absent commits" impression came from the stale clone only.
- No committed evidence was deleted at any point; AUD-51
  (`build_w24_cand_a/`) remains on disk untracked with its SHAs recorded.
