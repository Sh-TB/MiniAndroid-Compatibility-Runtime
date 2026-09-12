# REGRESSION — UNIFIED_008 (charter §27)

Every regression run on the FINAL binary (post throttle-split commit).

## Golden Real App (gmdice) — THE ACCEPTANCE JUMP

| check | UNIFIED_007 baseline | UNIFIED_008 now |
|---|---|---|
| launch | exit 0, 182,628 px | exit 0, 182,682 px |
| real UI from APK resources | 10 views, real strings | 10 views + **button texts from real DEX DiceSet.toString()**: `3D20 / 1d20 / 1d6 / 1d6+4` |
| tap dispatch | PROVEN | PROVEN (tap1=more-button AlertDialog path; taps 2-4 = dice buttons) |
| real DEX onClick chain | PROVEN (button_more path) | PROVEN through the **buttons[] array loop** (fixed array-length decode) |
| **visible state change** | **FAILED** (blocker: instance-array plumbing) | **PROVEN**: rolls `5·20·17 → 2·18·3 → 7·3·20 → 14·17·15`, per-tap px 182682→181715→181336→183485, 4 unique screenshots |
| artifacts | run/u007_golden_gmdice | run/u008_gmdice_final{,2}/journey/{journey.json,step_0*.png} |

## Telegram — ZERO REGRESSION + value upgrade

| stage | baseline SHA-256 (u007_telegram_v2) | regression run (u008_telegram_regr) |
|---|---|---|
| telegram_01_launch | 689fd1c5f3b0… | **IDENTICAL** |
| telegram_02_after_start_click | 42df72718b7e… | **IDENTICAL** |
| telegram_03_login_screen | 42df72718b7e… | **IDENTICAL** |
| telegram_04_after_next | 42df72718b7e… | **IDENTICAL** |
| telegram_05_final_state | e0932d37758a… | **IDENTICAL** |

Chain markers re-confirmed in stderr: `TL_auth_sendCode → EXP070-NET
interceptor`, `fillNextCodeParams`, `LoginActivity.loadCurrentState`.

Then the ARSC-value adoption upgraded the SMS screen: `getString(0xf10ff)`
now renders the REAL string `"Enter code"` instead of the field name
(run/u008_telegram_v3: 01 identical, 02–05 deliberately DIFFERENT —
upgraded content, chain intact).

## Font / audio / 3D / engine tests

| test | result |
|---|---|
| build/u007_font_proof | PASS — proof.png SHA `fad39aa17eb7ad55…` **identical to UNIFIED_007** |
| build/test_audio | **47 PASS / 0 FAIL** (MediaPlayer state machine incl. PLAYBACK_COMPLETED) |
| job server (u007) | unchanged code path (no edits) — E2E 10/10 from UNIFIED_007 stands |

## Corpus (14 real APKs, current binary)

| app | exit | nonwhite px | vs baseline |
|---|---|---|---|
| bgclock | 0 | 2,073,600 | same |
| chessclock | 0 | 23,472 | same |
| dooz | 0 (179s) | n/a | **same exit-0; +71% runtime** (deeper real interpretation of Compose app classes after throttle fix; framework cap unchanged) |
| gmdice | 0 | 183,935 | same |
| headingcalc | 0 | 0 | same |
| microtimer | 1 | 23,472 | **same as TRUE baseline** (00921c9 worktree rebuild also exits 1; NPE path pre-exists) |
| notes | 0 | 23,472 | same |
| openlauncher | 0 | 23,472 | same |
| simplekeyboard | 0 | 23,472 | same |
| simplestopwatch | 0 | 2,073,600 | same |
| stopwatch | 1 | 23,472 | same as baseline (exit-1 pre-existing) |
| tictactoe | 0 | 0 | same |
| tinymusic | 1 | 0 | same as baseline (corrupt EOCD, androguard concurs) |
| unote | 0 | 23,472 | same |

Regression methodology: the dooz/microtimer questions were settled by
rebuilding the TRUE baseline (00921c9) in a separate git worktree and
re-running — both behaviors reproduce there, so neither is a UNIFIED_008
regression.
