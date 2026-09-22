# S83 REPORT — GRAPHICS BASE COMPLETION + 23-GAME / 12-APP VALIDATION CAMPAIGN

Session: S83-GFX-BASE · Date: 2026-09-22 · HEAD before: 981e656e (S81) ·
Binary: rebuilt at S83 (83 MB, warnings unchanged)

## 0. Mission (user directive)

"همشون رو اجرا بکن تا بیس اصلی تموم بشه" — execute every remaining item so
the graphics BASE is complete; validate 10 simple apps + 20 simple games with
REAL screenshots; run L0/L1 apps at their best; test 1–2 random high-level
apps; COMPLETE the previous دوز (TicTacToe) and مار (Snake) games; deliver a
progress table; update GitHub per title.

## 1. What was done (executive summary)

1. **Runtime rebuilt from scratch** (build/ was empty post-reset) — 41
   translation units, link clean. Regression battery re-established: **26/26
   rc=0** before any change.
2. **TicTacToe Deluxe (دوز) built** — NEW 4th in-house game
   (`games/tictactoe-deluxe/`, 2 Java files + 4 resource files, pure
   android.jar): custom `GameView.onDraw` board (3x3 grid, hand-drawn X/O,
   win-strike, HUD, status), 9 cell buttons + NEW GAME + MODE toggle,
   vs-phone AI (win>block>center>corner law) on the main-looper Handler,
   deterministic LCG. APK: `tictactoe_deluxe_v1.0_vc1.apk`
   (sha256 16510d7c…). Tetris + 2048 APKs rebuilt from sources
   (cb2818df…, 1b1c602a…).
3. **Validation campaign executed** (`scripts/s83_campaign.py`): 23 games +
   10 apps + 2 high-level apps, every run's final frame real-captured and
   visually audited with the S81 instrument (R-NEW-402). **35/35 produced
   real PNG frames.**
4. **Six root-caused engine laws landed** (all semantic shadows / AOSP object
   laws — NO null/catch bypasses; regression-clean):
   - **S83 APX-ACT** — androidx/support activity trio semantic shadow
     (FragmentActivity.onCreate NPE + AppCompatDelegateImpl.ensureSubDecor
     ISE family, F-NEW-156): onCreate/setContentView/findViewById answered
     at the framework boundary with the AOSP-observable contract
     (U007 real inflation + F-023 parent-link + F-105b owner tags).
     Fanout: Mines premy uniq 2→37; 8 more titles reclassified rc=0.
   - **S83 CANVAS-GEOMETRY (P0)** — View.onDraw canvas now reports the
     VIEW's own bounds (w,h) instead of the framebuffer (1080×1920).
     Wrong-geometry family: apps centering content on cv.getHeight() drew
     against a phantom window and the replay clip amputated the lower half
     (TicTacToe board computed for y 477..1497 inside a ~790 px view).
   - **S83 LOCALE-DEFAULT** — `Locale.getDefault()` non-null singleton +
     accessor family (getLanguage/getCountry/…) with `__locale_tag__`
     (tobiasbielefeld solitaire attachBaseContext NPE).
   - **S83 INPUT-SERVICE** — `getSystemService("input")` → InputManager
     singleton, all 4 service tables (boxcars EbitenView NPE).
   - **S83 VIEW-TREE-OBSERVER** — `View.getViewTreeObserver()` non-null +
     listener family (ball2box/Godot ReportFullyDrawnExecutor NPE).
   - **S83 AUDIO-OBJECTS** — AudioAttributes$Builder / SoundPool$Builder
     fluent-this + build() object laws (astroloop SoundManager NPE).
5. **دوز completed end-to-end (real captures)**: X center opening → AI
   replies → mid-game → **O wins middle column with yellow strike** →
   "PHONE WINS!" + score 0:1 → round-over AlertDialog ("Round over /
   Phone wins! Score X 0 : 1 O (D 0) / NEXT ROUND") → round 2 fresh board
   with preserved score. 5 stage JPGs in evidence.
6. **مار re-proven at the new HEAD**: board ready → snake chasing apple →
   death → GAME OVER dialog → restart. 4 stage JPGs in evidence.
7. **Regression gates**: battery 26/26 rc=0 after EVERY law (4 rebuilds);
   frame_px spot values unchanged (f53 64042, f54 2073600 identical).

## 2. Honest results table

Games (23) — LEVEL = S81 visual audit of the final real frame:

| # | Title | Kind | rc | L | uniq | Note |
|---|-------|------|----|---|------|------|
| 1 | Snake Deluxe (مار) | in-house | 0 | L3 | 82 | full lifecycle re-proven |
| 2 | Mini Tetris | in-house | 0 | L3 | 70 | |
| 3 | TicTacToe Deluxe (دوز) | in-house NEW | 0 | L3 | 118 | complete loop captured |
| 4 | 2048 | in-house | 0 | L2 | 33 | static-state law (no taps in sweep) |
| 5 | TicTacToe Classic | real | 0 | L2 | 37 | |
| 6 | Mines (premy) | real | 0 | L2 | 37 | FIXED by S83 APX-ACT (was blank) |
| 7 | Balance the Ball | real | 0 | L2 | 14 | |
| 8 | Queens | real | 0 | L2 | 2 | Flutter engine boundary |
| 9 | Tarok | real | 0 | L2 | 2 | Flutter |
| 10 | Tirailleur | real | 0 | L2 | 2 | Flutter |
| 11 | Battleship | real | 0 | L2 | 2 | onCreate family, deeper root |
| 12 | Boxcars | real | 0 | L1 | 3 | InputManager fixed; GL viewport next |
| 13 | No Thanks! | real | 1 | L1 | 3 | Lifecycling CNFE escape (open) |
| 14 | Memory | real | 0 | L0 | 1 | inflated, paints blank — open |
| 15 | Blackjack | real | 0 | L0 | 1 | layout IS a full-screen WebView (honest) |
| 16 | Ball2Box | real | 1 | L0 | 1 | Godot GL after VTO fix |
| 17 | Halma | real | 1 | L2 | 2 | libGDX EGL (F-NEW-157 frontier) |
| 18 | Guandan | real | 1 | L2 | 2 | getChildAt-null chain (open) |
| 19 | Astroloop | real | 1 | L2 | 2 | Resources$NotFound after audio fix |
| 20 | Solitaire vayunmathur | real | 1 | L2 | 2 | androidx.window BigInteger (open) |
| 21 | Solitaire tobiasbielefeld | real | 1 | L2 | 2 | past Locale; Window.getCallback chain |
| 22 | Firestrike | real | 1 | L2 | 2 | androidx.preference XmlPullParser (open) |
| 23 | Dooz (compose) | real | 1 | L2 | 2 | Compose frontier (S39-S42 chain) |

Apps (10 + 2 high):

| # | Title | rc | L | uniq | Note |
|---|-------|----|---|------|------|
| 1 | uNote | 1 | L2 | 26 | renders; rc=1 on exit |
| 2 | Simple Stopwatch | 1 | L2 | 29 | renders |
| 3 | MicroTimer | 1 | L2 | 21 | renders |
| 4 | Notes (billthefarmer) | 0 | L2 | 6 | |
| 5 | gmdice | 0 | L2 | 51 | |
| 6 | Heading Calculator | 1 | L2 | 32 | renders |
| 7 | Chess Clock | 0 | L0 | 1 | intent-Uri null (app-own) |
| 8 | DeskClock | 1 | L2 | 2 | Context.getDataDir chain |
| 9 | Bnyro Clock | 1 | L2 | 2 | Application identity chain |
| 10 | P9 | 1 | L2 | 2 | libGDX EGL frontier |
| H1 | NewsBlur (HIGH random) | 1 | L2 | 2 | RecyclerView/fragment depth |
| H2 | TimeLimit (HIGH random) | 1 | L2 | 2 | high-level frontier |

## 3. Frontiers (honest, registered for next wave)

- Flutter-host games (queens/tarok/tirailleur): FlutterEngine surface chain.
- libGDX/Godot/Ebiten GL viewport (halma/p9/boxcars/ball2box): F-NEW-157
  family — EGL/EGL10 object law is the next single-fix fanout.
- Lifecycle deep chains: Lifecycling.generatedConstructor CNFE escape,
  androidx.window Version BigInteger, SafeIterableMap.remove iterator.
- WebView-only layouts (blackjack): no JS engine — permanent honest
  boundary unless a WebView surface is built.

## 4. Evidence

- `docs/evidence/s83/` — 44 JPGs ≤100KB (35 title finals + 9 gameplay
  stages) + SHA256SUMS (309 KB total).
- Raw frames: `run/s83_campaign/`, `run/s83_ttt_autoplay/`,
  `run/s83_snake_proof/`.
- Scripts: `s83_campaign.py`, `s83_build_games.sh`, `s83_build_tictactoe.sh`,
  `s83_ttt_autoplay.py`, `s83_snake_proof.sh`, `s83_evidence_package.py`,
  `s83_disasm_appcompat.py`.
