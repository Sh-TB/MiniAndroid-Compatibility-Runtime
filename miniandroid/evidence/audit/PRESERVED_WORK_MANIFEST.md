# PRESERVED WORK MANIFEST — nothing disappears

Every contribution referenced by the mission, with its preservation and
integration status. Full per-claim rows: ACHIEVEMENT_LEDGER.csv.

## Integrated in mainline (verified here)
- W22-W24 build architecture chain (FASTPROFILE, -g1, tiering W24TIERS=1,
  ABBA discipline, steal root-cause): commits 29a708c3 → 4ada9e3e → 68f4fe58
  → cfd0870e → d8b8fbb9; evidence/w22-w24 committed incl. raw logs.
- Wave-7 interpreter contract + wave-10 PIC profiles: Makefile rules verified
  unchanged under W24TIERS (make -n matrix, cfd0870e).
- BUG-1/1b OBJECT libraries, BUG-4 battery env fix, BUG-5 placebo law,
  BUG-8 parse-order fix: all FIXED + verified (ledger AUD-13/22/48/50).
- ccache opt-in warm path (25.4 s): evidence/w23 committed.
- Law-test battery (s1xx-s23x, 49 tests) + 5-APK screenshot-hash gate:
  executed TODAY on the W24 candidate — 49/49 + 11/11 IDENTICAL.
- #606 layout closure (closed, 17 comments) — gravity/dimension handling
  verified present in layout_inflater.cpp.

## Confirmed to exist but NOT in mainline (recovery list)
- RC-12 ScaleType oracle + probe (commits 46ca6258/73dcadb6/1439627a/d77edba6
  — absent from this repo; files absent). Recovery: obtain coder branch.
- #633 MG-011 one-line fix (`out->ok = err.empty() && !paths.empty();`)
  — absent from src/resources vector decode. Recovery: apply + parity test.
- #630/#631 ten layout test apps — apps/ empty in mainline. Recovery:
  re-add from coder trees, labeled diagnostic vs compatibility.

## Open defects preserved (confirmed live here)
- GridLayout absent (AUD-30), nine-patch npTc absent (AUD-32), FORTIFY 3
  symbols (AUD-34), BUG-7 duplicate shadow_registry.h (AUD-49),
  -Werror/CI gap (AUD-45), CMake WEBP parity gap (AUD-07).

## Rejected but preserved (with disproof)
- mold/lld, -gsplit-dwarf, ggc-min tuning, -fno-var-tracking-assignments,
  Ninja migration, PCH (×3), inline-budget params (BUG-5 placebo):
  REJECTED_AND_CORRECTED.md — each with the measurement that disproves it.

## Superseded
- Monolith 94k-line dalvik_engine.cpp claims: the split-path is default since
  W4; the monolith is retained only as DALVIK_SPLIT=0 fallback (AUD-25).
- #626 wave-10 dev-so speed numbers: partially superseded by W24 candidate
  dev-so measurements (268.98 s at candidate flags today); PR still open.

## Tracker states fetched today (2026-11-20, GitHub API as Sh-TB)
- 300 issues+PRs indexed; #618/#619/#620/#623/#606/#604 closed;
  #625 PR closed(merged); #626 PR open; #597/#610/#614/#621/#622/#624/
  #628/#629/#630/#631/#632/#633/#634/#586 open. Full index:
  audit session log /tmp/gh_issue_index.txt (content mirrored in the issue).
