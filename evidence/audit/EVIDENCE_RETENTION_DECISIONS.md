# EVIDENCE RETENTION DECISIONS — S-SLIM (2026-11-23)

Authority: CONSTITUTION_V2 §172 + docs/ARTIFACT_LIFECYCLE.md lifecycle law.
Doctrine applied: **local-first evidence** — new wave evidence stays untracked
(ignored `/evidence/`, `/docs/evidence/`) until an explicit reviewed
`git add -f` promotion against the size budget and the policy validator.
Tracked canonical evidence was NEVER touched except by the decisions below.

## Decision table (categories → actions)

| class (ARTIFACT_LIFECYCLE §3) | decision | what exactly | evidence |
|---|---|---|---|
| BUILD_ARTIFACT (gmon/prof) | UNTRACKED keep-local | 4 × gmon.out under miniandroid/evidence/w21/gprof (~19.7 MB) | SHA rows in S_SLIM_UNTRACK_SHAS.txt; regenerate via the w21 profiler recipe |
| RAW_LOG (run exhaust) | UNTRACKED keep-local | evidence/batch61x dirs: api_trace.json, view_tree.json, run.log, crash.log, frames/, exp031_5/, screenshot.ppm ×2 (11.9 MB) + download/batch614_624_evidence run artifacts | canonical report.md + screenshot.png kept tracked in the same dirs |
| RAW_API_DUMP (S230/S231 no-giant-export law) | UNTRACKED keep-local | evidence/s195_audit/comments_raw{,.partial}.json (identical twins) + issues_raw{,.partial}.json (~25.4 MB) | the fetch scripts (scripts/w22_fetch_more.py et al.) regenerate them; curated digest remains |
| DUPLICATE (byte-identical) | UNTRACKED losers, keep first | 15 groups: issue612 ftime ×11, s207 ttt ×2, frozenbubble ×5, docs gifs ×3, MessageSchema, make_err twins | DUPLICATE_AND_UNUSED_LEDGER.csv (sha256 + action per row) |
| BUILD_ARTIFACT (binaries) | DELETED (local tree) | miniandroid/build (6.7 GB) — regenerated in the clean-clone verification | rebuild recipe = Makefile (canonical); battery re-run in the clone |
| FORBIDDEN run-store residue | UNTRACKED | 56 + 37 files: *.db/-wal/-shm capture trees under evidence (tallybook databases), miniandroid loose *.db/logs | validator FORBIDDEN_CLASS list → S_SLIM_UNTRACK_SHAS.txt |
| SCRATCH_RESIDUE | DELETED | make_out4-12.txt, s203_out*.txt, s203_gate_out.txt, 3 × .rej in src/ | applied content lives in git history (patch already landed) |
| ROOT_STRAY | UNTRACKED | w_s241_androguard.json | root allowlist §172.2 is exact |
| APK (§20 zero-APK law) | UNTRACKED keep-local | download/batch614_624_evidence/de.tcrass.minos_10004.apk — the pinned corpus APK STAYS on disk (runtime evidence dependency) | sha af769233… recorded; corpus identity files untouched |
| DORMANT source copy | UNTRACKED keep-local | evidence/cont11/w8/fnew511_dalvik_engine_candidate.cpp (3.5 MB) | AUD-58: content verified present in main; SHA in ledger |
| stale local backup | DELETED | upload/_ma_local_backup (2.4 GB) + /tmp/my-project (410 MB) — superseded by origin/main + tag pre-slim-20261123 | recorded here |
| CANONICAL_EVIDENCE | KEEP tracked | all wave receipts: s27w4_matrix.tsv, w4_flip_r1 screenshots + trace summaries, coin-face pixel proofs, matrix CSVs, audit reports, S27_COMPLETE_* files | untouched; validator IMAGE baseline +12 entries pins their bytes |
| CANONICAL_FIXTURE | KEEP | fixtures/** incl. FreeSerif.ttf (3.5 MB) — consumers: s98_text_law_test, s243_font_pipeline_law_test, font_pipeline_probe | grep-verified consumers |

## Totals

- Tracked files: 17,956 → 17,4xx (see REPOSITORY_SIZE_AUDIT.md for the exact
  post-pass number); tracked bytes 339.1 MB → ~245 MB.
- 461 index removals staged; every untrack recorded by SHA-256 in
  evidence/audit/S_SLIM_UNTRACK_SHAS.txt (427 + follow-up rows).
- Zero evidence loss: every byte-identical duplicate removed had its SHA
  recorded; every untracked raw artifact stays on local disk.

## Promotion procedure (future waves)

1. Wave runs write evidence under evidence/s28*/ (auto-ignored).
2. Register the prefix in docs/PATH_OWNERSHIP.json approved_dirs (or the
   validator's frozen-snapshot check fails by design).
3. `git add -f` only: one report, one machine-readable summary, decisive
   screenshots, SHA ledger. Raw traces/logs/frames stay local.
4. Pre-commit hook + CI policy.yml run the validator; SIZE_BUDGET fails on
   growth beyond the re-adopted budgets.
