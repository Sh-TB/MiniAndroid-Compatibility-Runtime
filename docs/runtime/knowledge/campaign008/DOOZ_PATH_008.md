# DOOZ PATH — UNIFIED_008 (charter §6/§7, Target B)

## Ground truth established (all from the REAL APK)

- package `io.github.yamin8000.dooz` (GPL-3.0, F-Droid), 1 DEX, 16,869 methods
- **2,189 methods touch `androidx.compose.*`** across **446 classes**;
  packages used: compose/runtime, compose/ui, compose/foundation,
  compose/material3 — pure Jetpack Compose app, ZERO XML layouts
- real resources extracted from resources.arsc (via androguard oracle):
  `app_name="Dooz"`, `first_player_name`, `computer`, `about`,
  `dynamic_theme_notice`, `dice_rolling_start`, … (22 strings listed in
  run/u008_oracle/arsclib_dooz.txt: 11 types / 249 entries)

## Runtime status

| stage | status | evidence |
|---|---|---|
| dooz_01_launch | **PROVEN** | exit 0, DEX parsed, screenshot captured (run/u007_dooz_evidence, re-run in u008 corpus pass) |
| dooz_02_real_ui | **NOT_PROVEN** | Compose composition renders nothing — no View tree exists to inflate |
| dooz_03_after_touch | **NOT_PROVEN** | no rendered targets → hit-test has no Compose nodes |
| dooz_04_next_state | **NOT_PROVEN** | depends on 02 |
| dooz_05_result | **NOT_PROVEN** | depends on 02 |

## Why UNIFIED_008 did not fake progress here

The Compose execution model is fundamentally different from the View world
the interpreter already runs:

1. `@Composable` functions are D8-compiled into state-machine transforms over
   `Composer` + `SlotTable` (restartable groups, memoized lambdas `$r8$lambda`)
   — the "UI" only materializes as draw commands inside `Material3` draw
   scopes.
2. A minimal bridge needs: Composer/SlotTable replay, Recomposer + state
   snapshot system, `ComposeView`-equivalent draw surface wired to the
   software renderer, and Material3 `Button/Text/TextField` painters.
   JetBrains/Compose-Multiplatform shows the target architecture (its Skiko
   backend is exactly "Compose → Skia canvas"), but porting is a multi-month
   project, not a campaign item — and the campaign's own depth-first rule
   (§45/§41) forbids trading a real, completed Golden journey for a
   half-Compose.
3. The ADOPTED oracles (ARSCLib, Apktool, androguard) now give us a
   reproducible ground-truth pipeline for WHEN that bridge is built: the
   dooz resource table (11 types / 249 entries) and the Compose method
   census (2,189 methods / 446 classes) are machine-generated facts, not
   estimates.

## Decision

- Dooz stays **PARTIAL** overall: launch PROVEN, real-UI rendering BLOCKED
  with the precise architectural blocker above.
- Golden (Target A) delivered the §44 acceptance jump instead; Telegram
  preserved and upgraded.
