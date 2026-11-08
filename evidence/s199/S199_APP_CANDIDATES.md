# S199 APP CANDIDATES — evaluated on the S199 binary

Recorded: 2026-11-08 20:03 UTC. All candidates below are REAL corpus APKs located and
inspected this wave (no invented names). Depth = observed on 97628b00d237f9eb.

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


## NOTE — identity refresh (S199 close)
The S199 wave made two further source commits after the baseline was
written (F-NEW-619 typed-view parent chase at the f590 hook; F-NEW-620/
620b GL_ACTIVE_ATTRIBUTES=3 + glGetActiveAttrib canonical-name law).
The FINAL canonical S199 binary is 97628b00d237f9eb — goldens 3/3 ALL
HOLD and floor 11/11 CLEAN re-verified on it (this is the identity all
future waves compare against). The 619/620 laws did NOT yet move the
shape-attrib needle (glGetActiveAttrib never dispatched — the
fetchAttributes loop is gated deeper, at the AndroidGL20 real-native
path); that remains the named Coder-3 frontier with the evidence above.
