# MASTER AUDIT — Cross-Coder Achievement Audit (2026-11-20)

Mission source: upload/Pasted Content_1795175734014.txt (1040 lines, §0-§12).
Method: every mandatory section read line by line; each claim tested where the
environment allowed; verdicts assigned per the master-task taxonomy; nothing
accepted on trust — another coder's status is treated as a claim, not proof.

## Baseline manifest (taken before any modification)

- Repo: github.com/Sh-TB/MiniAndroid-Compatibility-Runtime, branch main,
  HEAD d8b8fbb9 (W24-B) at audit start; working tree clean before audit edits.
- Toolchain: g++ 14.2.0, GNU Make, Python 3; **cmake ABSENT** (tools/dl wiped
  by sandbox recycle) — CMake graph measurements are BLOCKED, not skipped.
- Host: 2 vCPU / 4 GB RAM / GCC 14.2.0, shared VM, hypervisor steal measured
  24-25% of every build window today (evidence/w24/RAW_LOGS/w24_combo_steal.txt).
- Tracker: 300 issues+PRs fetched from the GitHub API today; every issue
  referenced by the mission exists (#586-#634 incl. #625/#626 as PRs).
- No destructive cleanup performed; build trees and stale artifacts preserved.

## Verdict counts (reconcile with ACHIEVEMENT_LEDGER.csv, 50 rows)

- CONFIRMED (any level): 30 — incl. 3 fresh build-probe REJECTEDs recorded as
  preserved corrections, tracker-state confirmations, and today's ABBA/battery/
  gate run on the W24 candidate (d8b8fbb9).
- REJECTED: 4 (B4 mold/lld, B5 split-dwarf, B6 ggc-min, B7 var-tracking,
  EXP-B Ninja — external folklore does not reproduce on this tree).
- PARTIALLY CONFIRMED: 5 (§D gravity depth, §I ScrollView offsets, §L reference
  chain, MG-010 clip-path, #606 layout closure).
- BLOCKED: 4 (cmake graph measurement, RC-12 oracle commits absent, #628
  frames-12 exact APK, #597/#618/#619 APK corpus absent).
- PENDING: 3 (#634 source audit, UBSan profile, BUG-7 dedupe).
- NOT-INTEGRATED but CONFIRMED-to-exist-elsewhere: RC-12 oracle, #633 MG-011
  fix, #630/#631 layout apps.

## Key findings by mission section

### B1/B2 build findings (#632)
- QuickJS compiled twice in CMake (two OBJECT libraries) — CONFIRMED at
  source level; Makefile compiles once. CMake graph test BLOCKED (no cmake).
- Battery-test loop without EXCLUDE_FROM_ALL — CONFIRMED at source level.
- The NEW-9 retraction (guard at CMakeLists.txt:433) — CONFIRMED present.
- ~52 links + OOM claim — BLOCKED (no cmake); OOM NOT observed on the Make
  path (peak RSS 1221 MB / 4 GB across ~40 full builds W22-W24).

### B3-B9 experiments
- B3 ccache: CONFIRMED (committed logs: cold 553.42 s 0 hits / warm 20.94 s
  88/88; warm-cache identical rebuild 25.40 s).
- B4 mold/lld: REJECTED — link is 1.5 s of a 350 s build.
- B5 -gsplit-dwarf: REJECTED — +4 % slower on the heaviest TU (fresh ABBA probe).
- B6 ggc tuning: REJECTED — 3× slower (102 s vs 32 s, GC thrash). Preserved
  as a correction so it is never retried.
- B7 -fno-var-tracking-assignments: REJECTED — no win (GCC 14 fixed the VTA
  pathology; -g1 already drops var-tracking).
- B8 .DELETE_ON_ERROR: CONFIRMED missing → **added to the Makefile in this
  audit** + behavior demonstrated on a failed target.
- B9 job pools: CONFIRMED as a non-issue at -j2 (no OOM in any full build).

### Build architecture (W22-W24, independently re-verified)
- W24 tiering ABBA A/B: −17.3 % wall / −17.7 % CPU, battery 49/49, gate 11/11
  on candidate codegen — CONFIRMED (commit d8b8fbb9).
- BUG-8 parse-order defect: CONFIRMED + FIXED (cfd0870e).
- Steal root-cause: CONFIRMED (24 % of every window; scheduler exonerated ×2;
  Ninja rejected; candidate sits at the 288.4 s effective-capacity floor).
- Targets <280 s / <250 s: honestly MEASURED-MISS, documented.

### Runtime / apps
- TicTacToe #619 (closed): render parity re-proven TODAY on the W24 candidate
  (screenshot hash d55056a8... identical to canonical, 11/11 gate).
- #618/#623 closed per tracker; re-verification BLOCKED (APKs absent).
- #597 OpenCalc: BLOCKED at APK; 7×3=21 claim untestable here.
- #628 frames-12: BLOCKED (exact APK absent; substitute app shows no setGraph).
- #633 MG-011 fix: NOT INTEGRATED (proposed expression absent from source) —
  highest-value recovery candidate.
- RC-12 ScaleType oracle: NOT INTEGRATED (4 local commits absent from mainline).
- #630/#631 layout test apps: NOT INTEGRATED (apps/ empty).
- #586 FORTIFY: CONFIRMED (3 defined __*_chk symbols in the binary).
- §H GridLayout (no solver), §K nine-patch (no npTc handling): CONFIRMED live.
- Opcode law tests (#627): CONFIRMED (w15 law test + battery rc0 today).

## False-green / test-quality notes (§8 of the mission)
- The BUG-5 placebo lesson (page-cache order bias) is preserved in the
  Makefile comment: any future param claim must alternate run order.
- The battery never asserts exit code alone: 49 tests assert laws, and the
  5-APK gate compares screenshot SHA-256 hashes against a recorded canonical
  set (11/11 today) — no static placeholder screenshots involved.
- RC-12's verifier defect history (V-1/V-2) could not be re-audited here: the
  oracle files are absent from mainline (BLOCKED row AUD-26).

## Integration positions (§6 of the mission)
See INTEGRATION_MAP.md — every accepted contribution is placed on the shared
execution chain with its consumer stage.
