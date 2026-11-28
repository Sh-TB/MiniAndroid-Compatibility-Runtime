# MiniAndroid Showcase — the permanent public gallery

**Live:** https://sh-tb.github.io/MiniAndroid-Compatibility-Runtime/
**Offline zip:** https://sh-tb.github.io/MiniAndroid-Compatibility-Runtime/MiniAndroid-Showcase-Offline.zip
**Machine manifest:** https://sh-tb.github.io/MiniAndroid-Compatibility-Runtime/showcase_manifest.json
**Source of truth:** `docs/evidence/canonical/registry.json` on `main` @ `f1312668f`
**Generator:** `scripts/t279_build_showcase.py` (never hand-edit the HTML)

## What it is

A standalone, responsive HTML gallery generated from the canonical registry
(179 titles). Every image is a genuine MiniAndroid runtime capture of an
original release APK — no mockups, no stock images, no reconstructed app
faces. Historical captures and current reproductions are kept strictly
separate; a historical screenshot never proves today's engine.

## What it shows

- Statistics: 179 titles · 6 interactive (observable state change) ·
  7 current-reproducible (two independent runs, byte-identical faces) ·
  16 partial · 2 regressed (history preserved) · 2 blocked (frontier named).
- Search by name/package; filter chips by the 8-label current-status
  vocabulary (INTERACTIVE / CURRENT-REPRODUCIBLE / HISTORICAL-REAL /
  PARTIAL / REGRESSED / BLOCKED / PENDING / NOISE) and legacy registry
  statuses.
- Per-card historical-vs-current comparison images, click-to-enlarge
  lightbox, per-APK technical details (render level R0–R5, APK SHA256,
  engine commit + binary SHA16, last tested date, first divergence, notes,
  ledger/tracker issue links).

## Verification receipts (2026-11-28)

- Live render (headless Chrome): 179 cards, 73 images, stats exact
  (`179 | 6 | 7 | 16 | 2 | 2`); search "uturn" → 1 card.
- Offline mode: the zip's HTML embeds the manifest inline and localizes all
  image paths to `assets/` on the file:// boot path — 179 cards, 73/73
  LOCAL image srcs verified via file:// in headless Chrome.
- Zip read-back: downloaded from the Pages URL, SHA256
  `4e7ebc5c80a302795dd1a5d390c8f180ee2d7946e95dbe98e41a676147e1d56c` ==
  local build.
- All 73 manifest image URLs return HTTP 200 (raw main-branch paths; the
  T279 shots are tracked on main from `f9e1d3314`).
- Old pages preserved: `archive/s80/index.html` (the S80 proof page),
  `archive/prev-20261127-index.html` (the previous 8-record hand-curated
  showcase), plus the hand-curated `data/achievements.json` untouched.

## Storage law compliance

The runtime source tree (main) contains NO gallery HTML and NO screenshot
binaries beyond the tracked canonical evidence dirs; the gallery lives on
the separate `gh-pages` branch. Adding a future achievement =
registry row → regenerate the manifest/HTML with the generator → push
gh-pages. No hand-editing, no images in `src/`.

## Workflow to add a new achievement (repeatable)

1. Execute the original APK on the current build (two runs minimum;
   `scripts/t279_two_run.py` harness pattern), capture the frame census +
   screenshots.
2. Record the row in `docs/evidence/canonical/registry.json` (canonical
   schema + 8-label status) with the APK SHA256 and evidence paths.
3. Put the compact 480px captures in `evidence/t279/shots/` +
   `SHA256SUMS.txt` (tracked on main → the raw URLs become public).
4. Re-run `python3 scripts/t279_build_showcase.py` → commit the refreshed
   manifest/HTML/zip to `gh-pages` → push both branches.
5. Link the new registry row in the master ledger #472.
