# EXECUTION_MATRIX.md — S22 MASTER MISSION (ROOT CLOSURE + REAL APK EXECUTION)

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
