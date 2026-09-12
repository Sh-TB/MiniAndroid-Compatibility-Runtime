# MASTER CAMPAIGN 3 — §1 BASELINE MATRIX (RE-CAPTURE)

All values captured THIS session (2026-09-07) at the actual current HEAD.
No source modification preceded this capture. Zero assumptions inherited.

## Record (verified this session)

```text
HEAD:            d9625153 (main)  = docs(evidence) M3 phase-0 corpus matrix
Parent chain:    787b3f9e ← 938ad5a0 ← 916174fc ← 32d38b53 ← 97876119 ← 1aff4b97
                 ← 008573bd ← 2f91c63f ← 1df3b263 ← 5d8303e4 ← 83f1a04d ← c0f178a7 (origin/main)
Worktree:        CLEAN (git status --short empty)
Origin:          https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime.git
Remote main:     c0f178a7 (verified via git rev-parse origin/main)
Local/remote:    11 local commits ahead (M3 cluster 1+2 semantic fixes + docs)
Push status:     PUSH_BLOCKED — no gh CLI, no token file, no credential helper,
                 no env token (probed this session: gh auth status, git credential
                 fill, /home/z/.gh_token absent). Evidence payloads already
                 committed (938ad5a0 scripts/maintenance/post_m3_comments.py).
Toolchain:       g++ (Debian 14.2.0-19) 14.2.0; make (GNU); cmake ABSENT (build
                 is Makefile-driven — verified this session)
Build:           PASS — make -j full rebuild via scripts/test/run_test_battery.sh
Battery:         BATTERY GATE: ALL PASS (59 stages)  [was 55 at 1aff4b97; +4
                 stages upstream; battery is the regression authority]
```

## Golden hashes (sha256, this session)

```text
docs/history/golden-exp004/expected_object_model.json        0f6bfef5fa80fc0fb42d922301b1e88c4f9354cc711690bff5737520c71b524a
docs/history/golden-exp004/expected_screenshot_info.json     f20e991bdcc753970e26346b6f86f61cdc0f3ed4a016f6602af3618368607f3f
docs/history/golden-exp004/expected_view_tree.json           c6ae9877faaa65e03c4a12b8c1cff462b47394adb55e12f37c1553c73459dd24
miniandroid/golden/expected_api_trace.json   6ff761fa8cb1c10bcc4f6e97d35b431ca41ec60c1d2c0a4cc3ae40bb79667049
miniandroid/golden/expected_execution.json   f2887537c3b9fcaf1508391399a2f6ab768bed7b2d582b124d7e1515f17d1c40
miniandroid/golden/expected_objects.json     4ade2ed45695d737d458a4b4f858a681a6834cb327b904bc40919e1c479b912a
miniandroid/golden/expected_resources.json   a1bea7b486d0d075628853b209c17c2ea54693f4fffc1823333ff9ca34144a2d
miniandroid/golden/expected_view_tree.json   50120e009da4df7e43b2c07ae3515a4f625178f00154711d936fd15ea29b574d
```

## Corpus registry — 20/20 SHA-256 verified, ZERO drift vs phase0 records

Full per-APK hashes: `/home/z/my-project/logs/m3_corpus_sha_baseline.json`

| APK | sha256 (first 16) | drift |
|---|---|---|
| headingcalculator | (verified) | 0 |
| microtimer | (verified) | 0 |
| billthefarmer_notes | (verified) | 0 |
| muellerma_stopwatch | (verified) | 0 |
| simplestopwatch | (verified) | 0 |
| gmdice | (verified) | 0 |
| unote | (verified) | 0 |
| chessclock | (verified) | 0 |
| tictactoe | (verified) | 0 |
| openlauncher | (verified) | 0 |
| dooz | (verified) | 0 |
| bgclock | (verified) | 0 |
| simplekeyboard | (verified) | 0 |
| kiss | (verified) | 0 |
| bouncy | (verified) | 0 |
| scope | (verified) | 0 |
| survivalmanual | (verified) | 0 |
| coffee | (verified) | 0 |
| diary | 979e8cd8702ab5c0… | 0 |
| secuso_todo | (verified) | 0 |

## Phase-0 frontier snapshot (recorded at c0f178a7 pre-M3-fixes → re-run post-fix)

Post-fix rerun (`docs/evidence/m3_campaign/phase0/phase0_summary.json`):
18 SUCCESS · 1 PARTIAL · 2x-deterministic; headingcalculator 6.71% → 82.51%
nonbg (3x byte-identical); chessclock 2.71% → 0.68%.

Known-delta carried forward (§19/§13 targets, honestly not fixed yet):

| APK | Status | Root cause (named blocker) | Reusable layer |
|---|---|---|---|
| muellerma_stopwatch | PARTIAL rc=1 | FIND-G11-NOACTIVITY-001: QS-tile-only app, manifest has no launcher activity | EXP-031.5 assertion scoped to activity apps |
| secuso_todo | CRASH rc=-9 | ResourcesCompat.inflateColorStateList path | §13 color-state-list law |
| chessclock ticks | §9 scheduling proven (11 real-DEX ticks) | F-TIMER-COMPUTE: tick≥2 formatTime dispatch resolves to ActivityShadow — heap receiver records framework ancestor, not app class | constructor-time heap class identity law |
| chessclock color | — | F-ARGS: ChessClock.color(int) reaches Resources.getColor with resid=0 (app→framework int arg lost for this shape) | bridge arg-preservation law |
| microtimer | SUCCESS render, timer blocked | F-TIMER-STACK: La/e;.h indexes Thread.getStackTrace()[2]; synthetic stack returns 2 frames | synthetic shadow-dispatch boundary frames |
| bgclock/dooz/tictactoe | SUCCESS but nonbg=0.0% | pixel-audit bg heuristic (interaction goldens PASS separately) | audit interpretation, not runtime |

## Gate

BASELINE = known-good (battery 59/59, goldens unchanged, corpus 20/20, zero drift)
+ known-delta table above. Source modification may now begin.
