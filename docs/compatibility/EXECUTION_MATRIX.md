# docs/compatibility/EXECUTION_MATRIX.md — S22 MASTER MISSION (ROOT CLOSURE + REAL APK EXECUTION)

Updated: 2026-09-12 · Binary: F-076 build (active-cycle static-identity law) at 5a2b7d99+F-076

## Target matrix (Law 21) — no cell guessed; each has evidence

| Target | APK | Parse | DEX | Launch | UI | Frame | Draw | Pixels | Interaction | 3-run | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HelloWorld (golden §28) | helloworld fixture | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ golden 11e0056… byte-identical | N/A | ✅ byte-identical | CLOSED (maintained) |
| hello_color golden | rebuilt this session | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ non-white>0 golden | N/A | ✅ | CLOSED (§ battery) |
| TicTacToe (§29) | tictactoe.apk 760fe5ac… | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ golden | ✅ X→O→X WINS deterministic | ✅ | CLOSED (maintained) |
| Game-2: ChessClock | com.chessclock.android_29 5ca6f2c5… | ✅ | ✅ | ✅ rc=0 | ✅ | ✅ | ✅ | **2,073,600/2,073,600 (100%)** | timing-only app | ✅ SHA e4a2d7c90cd2fd26 ×3 | **VISIBLE EXECUTION PROVEN (S22)** |
| Game-2: uNote | app.varlorg.unote_30 be91103f… | ✅ | ✅ | ✅ rc=0 | ✅ | ✅ | ✅ | **236,520 non-white** | via corpus prior | ✅ | VISIBLE EXECUTION PROVEN |
| Game-2: dooz (Compose) | io.github.yamin8000.dooz_18 d81292cd… | ✅ | ✅ | ✅ rc=0→1 honest | children=1 | 0 | 0 | 0 (blocked by F-077) | blocked | ✅ SHA 31ddd4d5b8e6 ×3 | S22 FRONTIER — F-077 open |
| Simple Stopwatch | omegacentauri_26 | ✅ | ✅ | ✅ rc=0 | partial | 1 | partial | action-bar glyphs missing | n/a | ✅ | GATE H root queued (R-NEW-302 candidate) |
| **NEW S62+: anuto (source-first)** | built from source 8794573d… (github mjaun/android-anuto @ 33ed89e3) | ✅ | ✅ | ✅ rc=0 | ✅ real Application bound + onCreate + GameLoop.start | ✅ | ✅ REAL GameView.onDraw (C013 dispatched=YES) | ✅ 2,073,600 non-white (app-driven drawColor) | ✅ tap→GameView.onTouch dispatched, consumed=true (real DEX) | ✅ SHA 11a38a5aeeff45a6 ×3 | **L5 PROVEN + input→state dispatched** (sprites = canvas bitmap family, recorded frontier) |
| **NEW S62+: OpenSudoku (source-first)** | built from source 712b4a41… (github romario333/opensudoku @ d1914649) | ✅ | ✅ | ✅ rc=0, 0 errors | ✅ FolderListActivity + ListView + Button visible text | ✅ | ✅ | ✅ 2,029,440 non-white | ✅ 3/3 CLICK → real FolderListActivity$1 listener DISPATCHED | ✅ SHA 11671b9c439b2e10 ×3 | **L5 PROVEN + input dispatched** (button body = external http intent, honest no-op; DB rows = typed-zero data path) |
| **NEW S63: gmdice (source-first)** | built from source ee9f7396… (github ge0rg/gamemasterdice @ 6353926f) | ✅ | ✅ | ✅ rc=0, 0 errors | ✅ real GameMasterDice + ListView + "1d6/1d20/1d6+4" buttons + "..." AlertDialog painted | ✅ | ✅ | ✅ 1,744,539 non-white | ✅ 5/5 CLICK → real onClick → StandardDiceSet.roll → dice 6/5/3/2 (F-113) → setText | ✅ SHA fa1d8612 ×3 (frame pair 5312266e→fa1d8612, diff 1,584 px in result band) | **S10/L6 PROVEN source-first** (first repeatable input→handler→state→frame from a source build) |
| **NEW S63: siggen (source-first)** | built from source c83d21c6… (github billthefarmer/sig-gen @ master) | ✅ | ✅ | ✅ rc=0 | ✅ plain-Activity Main + FQCN-tag custom views (Scale/Knob/Display) + Sin/Squ/Saw buttons | ✅ | ✅ | ✅ 47,809 non-white (== S61 prebuilt count) | ✅ 5/5 CLICK → Main.onClick → R.id.sine case → audio.waveform mutation | ✅ SHA 7e5e14a3 ×3 | **S7** (audio-path state; custom-view measure 0x0 = recorded frontier) |

## Battery (Law 15 — honest)

- **91/92 PASS** at F-076 build. Single FAIL: GATE H real-APK image pipeline
  golden — settings/menu button crops show white=0 blue=0 while colors>8:
  the two PNG action-bar glyphs are not reaching the framebuffer. This is a
  REAL rendering gap (predates S22; S21 stash-bisect proved not-S21), NOT an
  environment gap. Registered as the next battery-focused root.
- EXT-01/EXT-02 environmental failures FIXED this session: fixture
  HelloWorldSelfAware-1.1.0-android.apk restored from the documented frozen
  URL with SHA-256 exact match 009b4671…, author reference screenshot
  restored (600×1067 grayscale, documented source) → EXT-01 9/9 PASS,
  EXT-02 CACHED-PASS.
- F-074 super-run stages PASS on the F-076 binary (no regression).
- §28 helloworld 26 checks PASS; §29 tictactoe PASS.

## S22 chain progress (park→wake→resume→…→pixels)

| Transition | S21 end-state | S22 now |
|---|---|---|
| runner parks on await-work | parked forever, silent | runner STARTS (F-076): E0.t→E0$a.t→F0.t loop proven live |
| wake/redispatch | never | initial composition drives invalidations; lifecycle replay runs |
| withFrameNanos → post #2 | never | blocked one hop upstream: initial composition crashes at F-077 before the frame request |
| Choreographer doFrame | never | pending F-077 |
| draw/pixels | 0 | 0 on dooz; ChessClock/uNote prove the render stack |

## Next blocker (exactly one broken transition)

F-077 (R-NEW-301): mutable-put buffer-fill in K/t.k/l/n/o writes bitmap bits
without the corresponding slot — initial composition dies at the first frame
request's doorstep. Probe live (MINIANDROID_S22_TRACE=1 → [TRIENODE] dumps).
