# FORENSIC VERIFIED WORK (issue #365)

Only rows whose required evidence standard is actually satisfied. Evidence was
re-derived independently during this campaign where possible; the strongest
block was **re-executed at current HEAD** (E5).

## V1. Re-executed at current HEAD during this campaign (E5)

| Item | Evidence (fresh, 2026-10-03) |
|---|---|
| Golden regression set | `scripts/working_vs_failing_probe.sh`: opencalc `e364b001ee7abd66` ×3, chess `b5a7a35d5fe0564b` ×3, dooz `d602648e8e401895` ×3, microtimer `da73010a37dd0189` ×3, unote `4f1a9e4e8f64fae8` ×3 — ALL PASS, byte-identical |
| Loading P0 probe contract | `scripts/loading_probe_runner.sh` 23/23 ALL PASS (write/read family, asset missing→FNFE, AFD bytes, alias, containment DENIED, prefs escape round-trip, WAL persistence, restart ×3) |
| Uninstall semantics (NEW) | `scripts/forensic_uninstall_proof.sh` 16/16 ALL PASS — closes the F-NEW-231 recorded PENDING row; two-package isolation, NOT_INSTALLED honesty, reinstall-clean |
| Canonical evidence law | `tools/verify_canonical_evidence.py` 0 FAIL (3 FAILs found + fixed this campaign; 150 titles, one artifact each) |
| Build law | full `make` clean build at HEAD (warnings-only) |

## V2. VERIFIED rows in the canonical ledger (30)

FR-010 HelloWorld, FR-013 Snake Deluxe, FR-014 dooz, FR-015 uNote, FR-017
GMDice, FR-018 MicroTimer, FR-019 Fish Rings, FR-021 Bouncy, FR-334 GAMES-1,
FR-335 Snake autoplay, FR-338 2048 autoplay, FR-339 Mini Tetris, FR-340
TicTacToe Deluxe, FR-341 GAMES-8 evidence package, FR-357–363 knowledge-
transfer chain (as issue-body documentation), FR-NI-002 loading master
execution (P0 scope), and the game/app-registry VERIFIED titles joined from
the canonical registries (incl. the 2 Mini Browser legs registered this
campaign). Full per-row evidence: `FORENSIC_ALL_REQUESTS_LEDGER.jsonl`
(`verified_status=VERIFIED`).

Representative evidence chains:

- **Snake Deluxe** (FR-013): in-house source `games/snake-deluxe/` → APK+SHA →
  execution session → 2 full runs + 4-run sweep → canonical GIF
  `docs/evidence/canonical/com.miniandroid.snakedeluxe.gif` → registry record.
- **Fish Rings** (FR-019): external F-Droid APK, 3 real taps → board paints →
  5-state interactive GIF (`eu.veldsoft.fish.rings.gif`, now the single
  canonical artifact) → S91 reproof matrix → ×3.
- **Mini Browser** (registered this campaign, R10 closure): real HTTPS GET
  example.com (HTTP 200, 559 bytes; 12,087 px state change; 3/3
  byte-identical) + z.ai 307-redirect leg; APK SHA `ee3cc2e6…`; GIFs on disk;
  README/ACHIEVEMENTS/CANONICAL_SCREENSHOTS synchronized.
- **dooz / uNote / MicroTimer / opencalc / chess**: golden SHAs re-verified ×3
  at HEAD (table V1) — the working-vs-failing explanations in
  `docs/WORKING_APP_LOADING_EXPLANATIONS.md` stand on these exact faces.

## V3. Working-vs-failing explanation (audited, not assumed)

The loading campaign's matrix (`docs/WORKING_VS_FAILING_LOADING_MATRIX.jsonl`,
8 rows) states that the working goldens stayed inside pre-campaign
capabilities (existing assets, ARSC resources, SQLite, prefs) and never called
the voided APIs — while failing-class white screens carry NON-loading
first-missing stages (`docs/WHITE_SCREEN_LOADING_ROOTS.md`: intro/auth nav
chain, deferred-UI family, window-root, compose/Hilt frontiers). This audit
re-checked the claim against the fresh traces: consistent. No white screen was
attributed to file loading without a trace.

## V4. Regression status

`docs/FORENSIC_REGRESSION_STATUS.jsonl`: 4 current-HEAD gate results + 2
historical justified re-baselines. REGRESSED count in the ledger: **0**.
