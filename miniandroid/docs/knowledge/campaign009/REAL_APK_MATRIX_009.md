# REAL_APK_MATRIX_009 — per-APK independent criteria (§33)

25 real APKs were downloaded and executed in this environment (15 pre-existing corpus + 10 new). APK binaries live in the EXTERNAL cache (`/home/z/.cache/miniandroid/apks/`, plus pre-existing `download/corpus/` working copies) — **zero APK binaries enter the deliverable archive (§31)**. Registry with SHA-256: `apk_matrix.json` + `tests/corpus/apks.json`.

Criteria are recorded **independently** — never collapsed to a single PASS (§33/§34).

## Pre-existing corpus (executed this session, regression-verified)

| APK | exit | non-white px | criteria status |
|---|---|---|---|
| Telegram 12.10.1 | 0 | 41,233 | PARSED ✓ DEX_EXEC ✓ UI ✓ TEXT ✓ (SMS screen, byte-identical to UNIFIED_002 baseline `b9b06072ea17d7fd`) |
| GMDice | 0 | 158,040 | PARSED ✓ DEX_EXEC ✓ UI ✓ STATE-Changing UI ✓ (byte-identical `26fc4116e4ba65b4`) |
| uNote | 0 | 23,472 | PARSED ✓ DEX_EXEC ✓ UI=fallback-screen (documented EXP-101: shared default screen) |
| bgclock | 0 | 2,073,600 | PARSED ✓ DEX_EXEC ✓ UI ✓ (fullscreen WebView-class render) |
| simplestopwatch | 1 | 23,472 | PARSED ✓, known exit=1 (manifest 0 activities per androguard) — unchanged |
| tinymusic | — | — | known corrupt ZIP (EOCD) — not re-run, unchanged |
| tictactoe / openlauncher / chessclock / microtimer / notes / simplekeyboard / headingcalc / stopwatch / dooz | 0 | (see EXP-101 matrix for details) | PARSED ✓ DEX_EXEC ✓ |

## New this campaign (10 APKs, all freshly downloaded + executed)

| APK (F-Droid) | category | exit | non-white px | seconds | PARSED | DEX_EXEC | UI_RENDERED(app-specific) | demand profile |
|---|---|---|---|---|---|---|---|---|
| Droid-ify v760 | I-Compose | 0 | 23,472 (fallback) | 27.1 | ✓ | ✓ | ✗ | 6,884 classes · 7,917 compose methods · 207 GLES refs |
| RetroWars v70 | K-3D libGDX | 0 | 23,472 (fallback) | 2.5 | ✓ | ✓ | ✗ | 11,355 classes · 268 GLES refs |
| Mindustry v1107 | K-3D libGDX | 0 | 23,472 (fallback) | 2.2 | ✓ | ✓ | ✗ | 6,119 classes · 255 GLES refs |
| Auxio v75 | H-Media | 0 | 23,472 (fallback) | 1.2 | ✓ | ✓ | ✗ | 4,490 classes |
| 2048 (PF) v100 | J-Game | 0 | 23,472 (fallback) | 2.6 | ✓ | ✓ | ✗ | 8,737 classes |
| KISS v224 | D-Lists | 1 | 23,472 (fallback) | 14.9 | ✓ | ✓ | ✗ | 1,620 classes |
| PF Notes v105 | B-Forms | 0 | 23,472 (fallback) | 2.9 | ✓ | ✓ | ✗ | 9,666 classes |
| Editor v198 | B-Forms | 0 | 23,472 (fallback) | 0.2 | ✓ | ✓ | ✗ | 319 classes |
| Shattered Pixel Dungeon v896 | K-3D libGDX | 1 | 23,472 (fallback) | 147.7 | ✓ | ✓ | ✗ | 3,119 classes · 177 GLES refs |
| NewPipe v1015 | H-Media | 0 | 23,472 (fallback) | 2.9 | ✓ | ✓ | ✗ | 10,671 classes · 7,162 compose methods · 251 GLES refs |

**Honesty note (§34)**: the 23,472-px render is the *shared default fallback screen* (documented EXP-101), NOT app-specific UI. No new APK achieved app-specific UI_RENDERED this campaign. The campaign's app-specific wins are elsewhere: §6 config matching (Telegram evidence) and §10 Compose chain (dooz structural progression). TOUCH_WORKS/STATE_CHANGE/NAVIGATION columns: not wired for the new apps — recorded as NOT RUN rather than claimed.

## Category coverage (§8 target vs actual)

| Cat | Target | Actual |
|---|---|---|
| A classic XML | ✓ | unote/notes/headingcalc/editor/pfnotes |
| B forms | ✓ | simplekeyboard/pfnotes/editor |
| C navigation | partial | openlauncher (fallback) |
| D lists | partial | kiss/newpipe (fallback) |
| E persistence | partial | unote (SQLite path exercised in earlier campaigns) |
| F timers | ✓ | microtimer/stopwatch/chessclock/bgclock |
| G network UI | ✗ | no new app progressed to network-boundary UI this session |
| H media | partial | auxio/newpipe downloaded+run; app UI not rendered |
| I Compose | ✓ | dooz (progression PROVEN §10), droidify/newpipe (profiled) |
| J game | ✓ | gmdice (STATE-proven), 2048, tictactoe |
| K 3D | partial | retrowars/mindustry/SPD downloaded+profiled; GLES route decided (PortableGL) |
| L WebView | partial | bgclock renders WebView-class fullscreen |

## §11 Dooz outputs status

`dooz_01_launch.png` = saved evidence (`run/exp_uc009_dooz/`): launch + composition-created tree (ComposeView→AndroidComposeView). `dooz_02_board/03_touch/04_state/05_result` = NOT ACHIEVED — blockers precisely documented (frame tick → first recomposition → onDraw → Canvas bridge).
