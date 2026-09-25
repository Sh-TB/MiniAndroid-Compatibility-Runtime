# EXECUTED GIFS — real MiniAndroid execution evidence index (S96)

> Every GIF below corresponds to a **REAL MiniAndroid execution** (real-dalvik run,
> SHA-pinned artifact, session record in the canonical registry). One canonical GIF
> per title (S84 law); earlier wave GIFs are kept as historical evidence and marked.
> The repo contains **no** upstream demo GIFs, promotional GIFs, generated fakes,
> static screenshots renamed to `.gif`, or other-emulator recordings — any such asset
> would be excluded here by law.

Machine links: [verified_executed_games.json](verified_executed_games.json) ·
[VERIFIED_EXECUTED_GAMES.md](VERIFIED_EXECUTED_GAMES.md) ·
[canonical/SHA256SUMS](evidence/canonical/SHA256SUMS) ·
validate: `python3 tools/verify_canonical_evidence.py`

## Legend

| Level | Meaning |
|---|---|
| E3 | runtime trace only (no meaningful visual) |
| E4 | real APK execution (single/recorded sessions) |
| E5 | deterministic repeated execution (recorded protocol) |
| E6 | corpus fan-out across APKs (law-level, not per-GIF) |

---

## VERIFIED EXECUTION GIFS (canonical, one per title)

| Title | Type | Status | Evidence | GIF |
|---|---|---|---|---|
| Snake Deluxe | game | VERIFIED | E5 · state change: YES · SHA `f2dd621c6625…` | [GIF](evidence/canonical/com.miniandroid.snakedeluxe.gif) |
| Mini Tetris | game | VERIFIED | E5 · state change: YES · SHA `927d966a5a73…` | [GIF](evidence/canonical/com.miniandroid.tetris.gif) |
| 2048 | game | VERIFIED | E4 · state change: YES · SHA `d613d30fce79…` | [GIF](evidence/canonical/com.miniandroid.g2048.gif) |
| MiniCraft (House Builder) | game | VERIFIED | E5 · state change: YES · SHA `3fbca3e4b1a1…` | [GIF](evidence/canonical/com.miniandroid.minicraft.gif) |
| TicTacToe Deluxe | game | VERIFIED | E4 · state change: YES · SHA `ade32b621e90…` | [GIF](evidence/canonical/com.miniandroid.tictactoedeluxe.gif) |
| TicTacToe Classic | game | PARTIAL | E4 · state change: YES · SHA `b6811a17d271…` | [GIF](evidence/canonical/com.emmanuelmess.tictactoe.gif) |
| Vector Pinball (bouncy) | game | VERIFIED | E4 · state change: YES · SHA `d96b48d7e866…` | [GIF](evidence/canonical/com.dozingcatsoftware.bouncy.gif) |
| ca.rmen.nounours | game | VERIFIED | E4 · state change: YES · SHA `24a19ed30eda…` | [GIF](evidence/canonical/ca.rmen.nounours.gif) |
| com.dozingcatsoftware.dodge | game | VERIFIED | E4 · state change: YES · SHA `5a648a244bec…` | [GIF](evidence/canonical/com.dozingcatsoftware.dodge.gif) |
| com.smorgasbork.hotdeath | game | VERIFIED | E4 · state change: YES · SHA `d6fdff53adfa…` | [GIF](evidence/canonical/com.smorgasbork.hotdeath.gif) |
| org.bobstuff.bobball | game | VERIFIED | E4 · state change: YES · SHA `788ce033de1a…` | [GIF](evidence/canonical/org.bobstuff.bobball.gif) |
| com.trianguloy.urlchecker (app) | app | VERIFIED-INTERACTIVE | E4 · state change: YES · SHA `ba1ae97c8e92…` | [GIF](evidence/canonical/com.trianguloy.urlchecker.gif) |
| Fish Rings | game | VERIFIED | E5 · state change: YES · SHA `f225a04b9187…` | [GIF](evidence/canonical/eu.veldsoft.fish.rings.gif) |
| Mini Browser | app | VERIFIED | E5 · state change: 12,087 px (real HTTPS fetch) · 3/3 byte-identical · SHA `454c1c5bd820…` | [GIF](evidence/canonical/com.miniandroid.browser.gif) · [record](evidence/s100_browser/README.md) |
| Mini Browser → z.ai | app | VERIFIED | E5 · tap Go → real TLS fetch of https://z.ai → 307 → chat.z.ai 200 (15,727 bytes, redirect followed via the S102 HEADER-OWS-TRIM law) · state change measured · SHA `ed20fd6219f2…` | [GIF](evidence/canonical/com.miniandroid.browser.zai.gif) · [S102 report](S102_REPORT.md) |

Interactive/state-change proven: **15/15** (every canonical GIF records click→state change).

## INTERACTIVE / STATE-CHANGE GIFS (detail)

| Title | What was executed | Input / state transition | Frames | Source project |
|---|---|---|---|---|
| Snake Deluxe | Full gameplay: 2 lives, 183 moves / 49 turns / 3 captures, game over x2, CJK dialog, restart (S79 matrix) | real-dalvik run, TouchDispatcher tap schedule (23 autonomous taps + death extension + restart tap @ (758,1022)); autoplay driver scripts/s80_sd_autoplay.py | 49 | in-house — games/snake-deluxe (source in repo) |
| Mini Tetris | Piece falls, NEXT queue advances; x3 deterministic runs at 6 unique frames/24 (S95) | real-dalvik run; START tap at (786,1854) (S95 protocol correction — old (540,1500) hit no touch target); autoplay driver scripts/s80_tet_autoplay.py | 75 | in-house — games/mini-tetris (source in repo) |
| 2048 | Tile merges advance SCORE to 200 across 65 frames (S80 autoplay) | real-dalvik run + autoplay driver scripts/s80_2048_autoplay.py (swipe-equivalent tap schedule) | 65 | in-house — games/2048 (source in repo) |
| MiniCraft (House Builder) | Terrain, 5 real placements, material cycle, DEMO builds a cottage, 2 digs; Blocks/Dug mutate (S86); x3 det runs (S95) | real-dalvik run; DEMO tap at (925,1862); build cursor walked via direction pad; BRICK cycles material; PLACE/DIG edit world | 15 | in-house — games/minicraft (source in repo) |
| TicTacToe Deluxe | O/X placement + turn flip (S83 tap schedule) | real-dalvik run + tap schedule on the 3x3 grid | 4 | in-house — games/tictactoe-deluxe (source in repo) |
| TicTacToe Classic | O/X placement captured (S83 click pass); S92 graphics verify FAILED -> PARTIAL | real-dalvik run + click probe; s83b click frames click_GAME-TTT-CLASSIC_CLICK_00..02.jpg | 3 | F-Droid com.emmanuelmess.tictactoe |
| Vector Pinball (bouncy) | Ball launch + score interaction (S62+/S85); S95: 3x WRONG_COLOR cleared, 1 clip residual | real-dalvik run, tap schedule (launch + nudge), ViewTree dump; S95 capture: 10 frames, 1080x1920 | 2 | https://github.com/dozingcatsoftware/Bouncy |
| ca.rmen.nounours | Tap swaps the drawn teddy-bear state (S84 click pass probed=1 state_changed=1) | real-dalvik run + click probe (probed=1 state_changed=1); S95 capture 10 frames | 2 | https://github.com/caarmen/nounours-android |
| com.dozingcatsoftware.dodge | New Game tap -> 13 live gameplay frames: bullets move, dodger visible (S84/S86) | real-dalvik run; New Game tap at (537,935); 14-frame canonical GIF = menu + 13 live gameplay frames | 14 | https://github.com/dozingcat/dodge-android |
| com.smorgasbork.hotdeath | Card-menu interaction, 3 state changes (S84); S95 vector/adaptive fix -> SEMANTIC_PASS | real-dalvik run + click probe (probed=6 state_changed=3); S95 capture 10 frames + verifier | 2 | https://github.com/jpriebe/hotdeath |
| org.bobstuff.bobball | Game-field interaction, 6/6 click state changes (S84); S95 PARTIAL(0) | real-dalvik run + click probe (probed=6 state_changed=6); S95 capture | 2 | https://github.com/bobthekingofegypt/BobBall |
| com.trianguloy.urlchecker (app) | Menu interaction captured (S85); core URL checks need NET-001 real networking | real-dalvik run + click probe (S85) | 2 | https://github.com/TrianguloY/UrlChecker |
| Fish Rings | 3 real taps on the external F-Droid APK: splash → timer transition (2,073,600 px) → empty board → TAP board paints (4,304 px) → TAP ring rotation (4,320 px) → TAP ring rotation (4,308 px); 5-state canonical GIF (S99) | real-dalvik run, tap schedule 184,184@30/40/50 (S91 protocol); frames run/s99/fish_gif/fish_tapseq; reproof docs/evidence/s91_fish_reproof/README.md | 5 | https://github.com/VelbazhdSoftwareLLC/FishRingsForAndroid |

## HISTORICAL / WAVE GIFS (real execution; superseded by or supplemental to canonical)

| Title | Path | Relationship to canonical | What it shows |
|---|---|---|---|
| Snake Deluxe | [snake_gameplay.gif](evidence/s79/snake_gameplay.gif) | distinct earlier run (S79 reproof matrix run_a/run_b; 70-frame GIF: game1/dialog/restart/game2) | Full gameplay with death + restart + CJK dialog; source of the S79 reproof record |
| 2048 | [g2048_gameplay.gif](evidence/s80/g2048_gameplay.gif) | byte-identical duplicate of the canonical GIF (S80 harvest source) | Autoplay run, 65 frames |
| Snake Deluxe | [snake_gameplay.gif](evidence/s80/snake_gameplay.gif) | byte-identical duplicate of the canonical GIF (S80 harvest source) | Autoplay run, 49 frames |
| Mini Tetris | [tetris_gameplay.gif](evidence/s80/tetris_gameplay.gif) | byte-identical duplicate of the canonical GIF (S80 harvest source) | Autoplay run, 75 frames |
| Snake Deluxe | [snake_head_gameplay.gif](evidence/s83b/snake_head_gameplay.gif) | distinct wave evidence (S83b 4-run head-close-up sweep; snake_head_run_00..03.jpg) | 4 repeated runs, head-region close-up |
| Snake (S73 autoplay instrument) | [snake_autoplay.gif](evidence/s73_snake_autoplay/snake_autoplay.gif) | distinct earlier-generation autoplay run (S73 harness, pre-S80 game) | 90-frame autoplay; superseded by the S80 Snake Deluxe instrument |
| HelloMiniAndroid demo fixture (NOT a game) | [demo_proof.gif](demos/demo_proof.gif) | distinct in-house demo-fixture execution (docs/demos/demo_manifest.json, 8 clicks dispatched) | Counter/timer demo: TAP ME button, count=1..8 state changes; fixture-class evidence |

## VISUAL-ONLY / LIMITED EVIDENCE

- None. Every GIF in the repository falls into the two sections above.
- Titles with JPG-only canonical screenshots (static verification, no GIF): see
  [VERIFIED_EXECUTED_GAMES.md](VERIFIED_EXECUTED_GAMES.md) §C/§D — 10 non-interactive
  VERIFIED games + 2 PARTIAL (TriPeaks, TicTacToe Classic has a GIF but contested visuals).

## Exclusions (explicit)

| Excluded class | Reason |
|---|---|
| Upstream project demo GIFs (e.g. F-Droid screenshots/phoneScreenshots) | not MiniAndroid execution |
| Promotional/marketing GIFs | not evidence |
| Generated/synthetic demos | never treated as execution (S92 anti-false-positive laws) |
| Static screenshot renamed `.gif` | all repo GIFs verified GIF89a multi-frame |
| Other emulator/runtime recordings | no such asset in repo |
