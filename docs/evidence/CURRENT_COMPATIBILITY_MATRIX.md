# CURRENT_COMPATIBILITY_MATRIX — §14 app-by-app, evidence-linked

Campaign: REUSE-FIRST FULL COMPATIBILITY + RESEARCH-TO-CODE
Date: 2026-09-05 · Local HEAD: `9e7c0e9b` · build PASS · all entries
re-verified at current HEAD or carry the exact HEAD of their last
runtime evidence (previous claims are hypotheses until current HEAD
proves them; entries not re-run THIS campaign are marked with their
evidence HEAD).

## Status vocabulary (§42 — no conversions allowed)

VERIFIED (runtime evidence at the cited HEAD) · PARTIAL · BLOCKED ·
NOT_TESTED. Nothing may be upgraded by static analysis or agent claims.

## Progression ladder (§13/§14)

| # | APK | BOOT | ACTIVITY | VIEW | RESOURCE | FONT | DRAW | INPUT | STATE CHANGE | SCREENSHOT | Status | Evidence HEAD |
|---|-----|------|----------|------|----------|------|------|-------|--------------|------------|--------|---------------|
| 1 | helloworld_golden (own fixture) | PASS | PASS | PASS | PASS | PASS | PASS | n/a | n/a | PASS | **VERIFIED** | 9e7c0e9b (re-run ×2 this campaign) |
| 2 | tictactoe_golden (own fixture) | PASS | PASS | PASS | PASS | PASS | PASS | PASS 9/9 | PASS (X→O→X WINS) | PASS | **VERIFIED** | 9e7c0e9b (re-run ×2 this campaign) |
| 3 | simplestopwatch | PASS | PASS | PASS | PASS (ARSC-first) | PASS | PASS | n/a | PASS (BASELINE_MATCH pixel-exact) | PASS | **VERIFIED** | 738ac50 (u011 matrix) |
| 4 | gmdice | PASS | PASS | PASS | PASS | PASS | PASS | click evidence | partial (dice state) | PASS | PARTIAL | ad95d928-era campaign014 + u011 |
| 5 | unote | PASS | PASS | PASS | PASS (gravity-law improved) | PASS | PASS | n/a | n/a | PASS | PARTIAL (layout parity still narrowing) | 738ac50 (u011 matrix, documented improvement) |
| 6 | dooz / tictactoe (corpus variant) | PASS | PASS | PASS | PASS | PASS | PASS | click evidence | click evidence | PASS | PARTIAL (interaction matrix narrower than golden #2) | campaign014 sheets + u011 |
| 7 | chessclock, microtimer, bgclock, notes, heading, simplekeyboard, openlauncher, droidify, bouncy | PASS-level boot + render evidence | | | | | | | | | PARTIAL (per-app details: docs/research/APP_COMPATIBILITY_REGISTRY.md + campaign014 sheets) | ad95d928-era campaign014 |
| 8 | Telegram | PASS | PASS (onCreate path) | partial | partial (multi-DEX resources) | partial | partial | BLOCKED | BLOCKED | partial | **BLOCKED** (deep UI; EXP096 login-mock evidence exists) | eb55fa2-era EXP096 (metrics.json recovered this campaign) |

## Execution scoreboard (§37 — before → after THIS campaign)

| Stage | Before campaign | After campaign |
|---|---|---|
| APK_LOAD | PASS | PASS |
| MANIFEST | PASS | PASS |
| APPLICATION_BOOT | PASS | PASS |
| ACTIVITY_BOOT | PASS | PASS |
| DEX_EXECUTION | PASS | PASS |
| ANDROID_API_DISPATCH | PASS | PASS |
| RESOURCE_RESOLUTION | PASS | PASS |
| ARSC | PASS | PASS |
| LAYOUT | PASS | PASS |
| MEASURE | PASS | PASS |
| FONT | PASS (Cases A/B/D/E VERIFIED; C open-blocked; F spec-pinned — see font doc @ fe5e5ba) | PASS (unchanged) |
| CANVAS | PASS | PASS |
| RENDER | PASS | PASS |
| SCREENSHOT | PASS | PASS |
| INPUT | PASS (golden #2) | PASS |
| CLICK | PASS 9/9 | PASS 9/9 |
| MULTI_FRAME | PASS (10 frames) | PASS |
| DETERMINISM | PASS | PASS |
| HELLO_WORLD | PASS | **PASS (revalidated ×2 at current HEAD)** |
| TIC_TAC_TOE | PASS | **PASS (revalidated ×2 at current HEAD)** |
| STRING_POOL_MUTF8 | NOT_TESTED (implicit raw-bytes) | **PASS (7/7 battery; corruption bug FIXED — FIND-REUSE-001)** |
| SWITCH_PAYLOAD_IS_DATA | implicit | **PASS (explicit WINEDROID-011 discriminator)** |
| ARG_ZERO_FILL_LAW | NOT_TESTED | **PASS (determinism pinned — WINEDROID-007)** |

## Honest gaps (not blockers for the golden milestones)

- Telegram full UI: BLOCKED (multi-DEX resource resolution depth,
  rtl/locale plumbing, large view trees) — EXP096 evidence shows a
  login-screen mock chain; real Telegram UI remains open.
- Corpus-wide interaction parity: only the golden fixtures have the full
  §29 interaction ladder; corpus apps have click-evidence sheets only.
- u011 matrix hash set is pinned at 738ac50; re-run it after any
  layout/font change (this campaign changed none).
