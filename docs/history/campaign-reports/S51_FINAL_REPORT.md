# S51 FINAL REPORT — CANONICAL GITHUB PURGE + RUNTIME / GAME / AGENT CERTIFICATION

Head: `b80ae739` (21 commits ahead of origin/main, push BLOCKED by credential policy — unchanged law).
Every number below was produced at this head; states use only
IMPLEMENTED/TESTED/OBSERVED/REPRODUCED/RESEARCHED/BLOCKED/PENDING/UNVERIFIED.

## A. GitHub cleanliness

| Metric | Value | State |
|---|---|---|
| Tracked tree | 3,4xx files ≈ 11.6 MB source; max file 1.49 MB (src); **0 APK/log/trace/dump tracked** | VERIFIED-CLEAN |
| `.git` | 623 MB (packs 492 MB) — historical blobs only (78 × >8 MB ≈ 1.65 GB uncompressed: llvm-mingw 83.9MB, Telegram.apk 82.7MB, call_graph 65.5MB) | PARTIALLY-VERIFIED (weight = history; rewrite = PROPOSAL-ONLY, authorization required) |
| Remote refs | main + 4 archive branches; 7 tags/releases; LFS not used | VERIFIED |
| Issue/PR attachment sweep | GitHub API rate-limited unauth → not fully swept | PARTIALLY-VERIFIED (commands recorded for credentialed re-run) |
| Full backup (user demand: "check the full GitHub backup too") | `git clone --mirror` = 506 MB all-refs at `/home/z/archive/s51_full_mirror`; contents = history above, nothing extra | VERIFIED |

## B. Cleanup executed this session

No new purge required: tree was already clean (PHASE 0 re-verified). No history rewrite
(law). v0.0.6 checksums re-verified EXACT (prior session, reproduced). Worktree stays
≈285 MB incl. untracked build dir (262 MB, rebuildable, `make clean` law intact).

## C. Runtime certification (S51)

| Proof | Result | State |
|---|---|---|
| R-NEW-372 wrapper `.TYPE` law | `s51_2dprobe`: outer-null=false / inner-null=false / v=X; `[R372-TYPE]` fires; `new char[6][7]` obeys JVMS multianewarray via d8 lowering | TESTED (fixed) |
| **R-NEW-361 Dooz launch** | ROOT CAUSE PROVEN + FIXED: depth-80 backstop silently refused the ScatterMap Empty-fill helper (`Ln/a;.r` = Intrinsics + `Arrays.fill([JIIJ)`) at depth exactly 80 → zero metadata → sentinel-over-zeros `0xff00000000000000` → SWAR probe spin. Fix: dedicated 512MB interpreter stack + backstop 512 + `[R361-DEEP-REFUSE]` diagnostic. Post-fix: **v18 exit 0 / Status SUCCESS — first campaign completion**; zero HALT-LOOP | TESTED (fixed) |
| Dooz v18 first frame | framebuffer still blank (Compose drawing pipeline) | BLOCKED (next frontier, registered) |
| Dooz v23 | PARTIAL SUCCESS, 1 frame; ONE residual face `Lbw0;.d` + depth-512 `Lbp1;.<init>` chain | PENDING (R-NEW-373) |
| chessclock / unote (real F-Droid APKs) | exit 0 / SUCCESS, real UI rendered (unote texts legible) | TESTED |
| Sandbox close/reopen persistence | `s50_sandbox_test.sh` ALL PASS (20/20, 4 runs, deterministic fresh-state) | TESTED |

## D. Lifecycle

`PROCESS_CREATED → RESUMED` chain intact (battery G07 25-check state machine + S50
sandbox protocol re-run at S51 head). Close = process exit after final frame; finish()
cascade law covered by battery. Reopen + cross-root isolation re-proven (run1==run4
byte-identical, run1≠run2).

## E. Agent certification

| Game | Level reached | Evidence |
|---|---|---|
| TicTacToe | **L3 AGENT-PLAYABLE** (re-verified at S51 head) | golden 8/8, replay `613cfccc…` |
| **Connect Four (new)** | **L3 AGENT-PLAYABLE** | `validate_connectfour_golden.sh` 8/8 + `docs/evidence/solved/S51_AGENT_C4.json`: 24-step schema (observation/detected_state/chosen_action/input/prev-hash/new-hash/state_changed), 22/24 real state changes, hash chain continuous, win at step 22 (diag (0,3),(1,4),(2,5),(3,6)), gameOver frozen tail |
| gmdice | L2 runtime-playable (battery + tap goldens) | TESTED |
| Dooz | L0 (blank frame → nothing observable) | PENDING on render frontier |

Multi-step law: proven (≥2 consecutive state-changing steps across 22; observe→act→
re-observe loop closed by hash chain).

## F. Bugs this session

| ID | Root cause | State |
|---|---|---|
| R-NEW-372 | wrapper-class `.TYPE` unseeded → every d8 primitive multianewarray null | VERIFIED-FIXED (registry 353) |
| R-NEW-361 | depth-80 silent refusal starved ScatterMap Empty-fill (chain above) | VERIFIED-FIXED (open_frontiers −1) |
| R-NEW-373 | v23 residual `Lbw0;.d` + 512-chain `Lbp1;.<init>` | OBSERVED-FAIL (probes listed) |
| ConnectFour fixture doc error | header predicted win at click 24; real dispatch logs prove click 22 (diag (0,3),(1,4),(2,5),(3,6)) | CORRECTED |

## G. Battery

**ALL PASS 94/94 × 3 runs** at fix head (reproducibility gate; `/tmp/b51_run{1,2,3}.log`;
`docs/testing/BATTERY_INDEX.json` head refreshed). No test skipped or removed.

## H. Git

Tree clean; 21 unpushed commits (push BLOCKED — no credentials in env, per policy;
pre-commit secret guard PASS on every commit this session). Registry 354 roots;
open frontiers: R-NEW-228/303/323/330/331/335/373.

## Success criteria scorecard (briefing §DEFINITIVE)

1. Repo truly light: source tree yes; history weight = documented, rewrite needs approval — **PARTIAL (by law)**
2. Full backup audited — **VERIFIED** (506 MB mirror, contents accounted)
3. Runtime runs real APKs end-to-end — **IMPROVED (v18 first completion; render frontier open)**
4. Agent plays ≥2 games multi-step — **PROVEN** (TicTacToe + Connect Four)
5. Battery 94/94 ×3 — **VERIFIED**
6. No large new logs/less evidence discipline — **VERIFIED** (all new evidence = compact cards + bounded probes)
