# S199 APP CANDIDATES — evaluated on the S199 binary

Recorded: 2026-11-08 20:03 UTC. All candidates below are REAL corpus APKs located and
inspected this wave (no invented names). Depth = observed on 414332acd3603dac.

| App | APK | Architecture | Observed depth this wave | Blocks |
|---|---|---|---|---|
| microtimer | canonical_apks/dubrowgn.microtimer_8.apk | View/Service timer, no GL | 0 uncaught, 0 boundary, REAL_APP_CONTENT ×2 | none observed |
| opencalc | opencalculator_53.apk | View calculator, history DB (Room/SQLite) | 0 uncaught, 1 boundary, REAL_APP_CONTENT | the 1 boundary (persistence path) |
| chessclock | chessclock_29.apk | View + service | 0 uncaught, 1 boundary, REAL_APP_CONTENT | the 1 boundary |
| gmdice | canonical_apks/de.duenndns.gmdice_8.apk | View + preferences | INTERACTIVE PROOF holds (5 taps → 5 states, rerun identical) | none observed |
| tictactoe | canonical_apks/com.emmanuelmess.tictactoe_3.apk | libGDX GL + FreeType font | APP-OBSERVED: real font glyphs rasterized, input dispatched, game loop alive | shape-renderer VBO attrib bind; per-frame re-render |
| pf2048 / pfmemory | fdroid_batch / canonical_apks | libGDX/large assets | NO_ROOT (S195 baseline unchanged) | earlier chains |

## Selection per mission §4
- **Target A (best probability of full end-to-end): microtimer.** Cleanest
  cohort profile (0 uncaught / 0 boundary / REAL_APP_CONTENT), View-based,
  core feature (timer start/stop/lap) is a small, objectively testable
  input→state→frame loop. NEXT: define the core-feature acceptance script
  (start→running display→lap→reset) and run the 3-clean-run battery.
- **Target B (different architecture): tictactoe** — the GL/libGDX
  architecture validating the native chain (this wave's work). Its
  remaining board-render gap is the named frontier; microtimer does not
  depend on it.

Interpretation vs facts: the "blocks" column records observed first
divergences only; nothing here is a completion claim.
