# S81 REPORT — REAL APP VISUAL COMPATIBILITY & 200-ITEM OPEN-SOURCE CORPUS

Wave: S81 (user spec: "S78 — REAL APP VISUAL COMPATIBILITY & 200-APP
OPEN-SOURCE CORPUS CAMPAIGN" — numbered S81 after S78/S79/S80 execution).
Date: 2026-09-22. Base: d37e7f38 (S80 final).

## 0. The new law (§1, §52)

EXECUTED ≠ VISUALLY COMPATIBLE. From this wave, "app ran" is not an
achievement by itself. The accepted chain is
SOURCE → APK → LOAD → FRAMEWORK → VIEW → RESOURCE → DRAWABLE/BITMAP →
COLOR → LAYOUT → RENDER → INPUT → STATE CHANGE → SECOND RENDER →
REFERENCE COMPARISON → HUMAN REVIEW.

Status ladder (§17): L0 LOADED_ONLY · L1 NONBLANK · L2
GRAPHICALLY_NONTRIVIAL (here: GRAPHICALLY_INCOMPLETE when flags contradict) ·
L3 STRUCT_CANDIDATE · L4 SEMANTICALLY_CORRELATED · L5 VISUALLY_VERIFIED.
L5 is human-review-only (§48); nothing in this wave claims L4/L5.

## 1. Disk guard first (§32–§34) — P0

Entry disk: 98% used, 205 MB avail — CRITICAL (NO_NEW_BATCH zone).
Safe cleanup (stale S35-era run outputs, old probe logs, autoplay raw
frames — canonical evidence untouched in docs/evidence): 98% → 33%
(6.3 GB free). DISK_AVAILABLE recorded before BATCH-01 (5.8 GB) and after
(5.1 GB). No canonical evidence deleted.

## 2. Instrument: the S81 visual audit (§2, §3, §17, §36)

`scripts/s81_visual_audit.py` + `scripts/s81_run_and_audit.py`:
- Metrics: SCREEN W/H, UNIQUE_COLORS, COLOR_ENTROPY, DOMINANT_COLOR_RATIO,
  SECOND_DOMINANT_RATIO, LUMINANCE/SATURATION ranges, NON_BACKGROUND_*,
  region classes (textish/widgetish/imageish/iconish) with bounding boxes
  for View-tree correlation (§18).
- Detector flags: MONOCHROME_LIKE, LOW_COLOR_VARIETY, FLAT_BACKGROUND,
  TEXT_ONLY_UI, IMAGE_RICH, ICON_PRESENT, GRAPHICALLY_NONTRIVIAL,
  MISSING_IMAGES_SUSPECTED, IMAGE_DECODED_VS_RENDERED_GAP (APK raster
  count vs screen image pixels — §20/§26).
- Levels 0–5 derived ONLY from flags + structure; thresholds are in-file
  constants; NO single numeric score (§36).

## 3. Audit result: the user's complaint quantified (§39, §49)

18-APK curated ladder at HEAD (`run/s81_audit/s81_visual_report.json`):
- ZERO third-party apps reach L3. Only S80's own games do (Snake Deluxe,
  Tetris: ICON_PRESENT + GRAPHICALLY_NONTRIVIAL).
- 9/14 third-party apps MONOCHROME_LIKE or LOW_COLOR_VARIETY (gmdice
  dom=0.91, Notes uniq=6, Simple Keyboard uniq=2, Dooz uniq=2...).
- 7 apps flag IMAGE_DECODED_VS_RENDERED_GAP (24–32 rasters shipped,
  0 image/icon pixels on screen).
- 7 prior HUMAN_VISIBLE statuses DOWNGRADED per §39 — recorded by the
  generator in `docs/audit/APP_MATRIX.md` (S81 VISUAL_* columns added, §35).

## 4. Root causes + fixes (§41–§43) — REPRODUCE → ROOT CAUSE → LAW → FIX → TEST → OBSERVE → REGRESSION

### VF-NEW-001 / VF-DIALOG-ITEMS — ROOT_CAUSED-FIXED
- REPRODUCE: `fixtures/s81_visual_probe` (4 timed phases: XML resources /
  dialog / ListView / Toast). Phase-1 dialog painted title+message with
  `[DIALOG-LAYOUT] items=0` — `setItems` array dropped.
- ROOT CAUSE: `DialogShadow::dispatch_builder` recorded only item_listener.
- LAW: AOSP AlertDialog.Builder.setItems — the CharSequence[] elements BECOME
  the item list.
- FIX: materialize heap array elements ("array[i]" fields) into
  DialogWindow::items in BOTH dispatch layers (try_shadow_dispatch +
  bridge_to_api — R-NEW-339 dual-view shape). Listener recording preserved.
- OBSERVE: `materialized 3/3 items`; dialog 920x144 → 920x408; ITEM-A/B/C
  rows with dividers painted (evidence before/after JPGs).
- REGRESSION: battery 26/26, fidelity BYTE-IDENTICAL 90/90, f152 6/6,
  f153 3/3, spot pixel-golden 4/4. Zero golden deltas.

### VF-NEW-002 / VF-PLACEHOLDER-GARBLE — ROOT_CAUSED-FIXED
- OBSERVE: Notes + Simple Stopwatch screenshots had overlapping unreadable
  strings at top-left.
- ROOT CAUSE: C013-CUSTOMVIEW placeholder drew the raw class descriptor
  (e.g. "Lorg.billthefarmer.markdown.MarkdownView") as visible text over a
  1080x1920 region. (MINIANDROID_TEXT_TRACE probe added to locate: the only
  view text was the bottom bar — the garble was engine-drawn, not app-drawn.)
- FIX: neutral small "custom view (not rendered)" marker at bottom-left,
  both placeholder sites; class name stays in stderr only.
- OBSERVE: Notes frame clean after fix.
- REGRESSION: same green set; fidelity replay contains no placeholders.

### Probe results (fixture truth table)
- XML ImageView src (raster PNG): RENDERED ✔ (96dp)
- TextView textColor=@color ref: RENDERED ✔
- Programmatic setImageResource: RENDERED ✔ (EXP-067 chain works)
- Button background=shape drawable: PARTIAL (text painted, shape bg offset
  — recorded, not fixed this wave)
- AlertDialog title+message: RENDERED ✔ (bitmap-font style)
- AlertDialog setItems: WAS BROKEN → FIXED (VF-NEW-001)
- Toast: RENDERED ✔ (bottom dark box)
- (ListView phase ran under the undimmed dialog — deferred to next probe v2)

## 5. The 200-item F-Droid corpus (§4–§12, §15, §31, §45)

`docs/corpus/s81/corpus_index.json` (+ corpus_summary.csv). CORPUS_SEED =
"S81-CORPUS-SEED-2026-09-22"; selection = stable sha1(pkg+seed) ranking
(reproducible, §15). Index-first: NO blind APK downloads (§31).

- Mandatory §7 entries with full provenance (package page scraped live):
  - P9 — se.tube42.p9.android — v0.1.1 (vc11) — source
    https://github.com/tube42/9p — reference screenshot URL recorded.
  - TimeLimit — io.timelimit.android.aosp.direct — v7.7.1 (vc231) — source
    https://codeberg.org/timelimit/timelimit-android — reference screenshot
    URL recorded.
  - Status: DISCOVERED (honest: not executed this wave).
- Stopwatch category inventory: 16 packages (§8).
- Platformer category inventory: 10 packages (§9).
- GAMES_100: 100 items from live-verified game category slugs
  (puzzle-game/board-game/card-game/action-game/casual-game/platformer-game/
  shooter-game/educational-game → 184-pool).
- APPS_100: 100 items from 13 app slugs (326-pool).
- BATCH_PLAN: 4 × 25 mixed batches.

## 6. BATCH-01 — 25 fresh F-Droid APKs (§13, §14, §32, §33)

Mixed subset (5 simple / 5 mid / 5 visually-rich / 5 games / 5 high-value).
Per APK: version resolved via F-Droid API, SHA256 + size recorded (§32),
run at HEAD (8 frames × 300 ms), visual audit of last frame, small retention
(last frames + log only, §33).

RESULT: 20/25 RENDERED · 1 RENDERED_PARTIAL · 4 LOADED_RC1 (no frames) ·
1 DOWNLOAD-FAIL (retried: transient). Disk 5.8 → 5.1 GB (guard OK).

### F-NEW-156 — the dominant frontier (OBSERVED-FAIL, P0)
19/25 fresh apps render uniq=2 (blank) with the same signature: a first NPE
inside app `onCreate` (before/at setContentView) → APP BOUNDARY unwind →
nothing inflated. Faces: solitaire GameSelector.onCreate invoke#3,
heading-calculator MainActivity.onCreate invoke#6 (MainActivity$1.<init>),
chessclock onCreate invoke#2, simplestopwatch onCreate invoke#18
(findViewById null → downstream NPEs). The fresh corpus is HARDER than the
curated one (modern layouts, app-classes constructed pre-inflation) —
exactly what the campaign exists to expose. Each face queues for the §43
chain (disasm: `scripts/s81_disasm_probe.py`).

## 7. Registry / matrix / issues

- root_registry.json 413 → 417: VF-NEW-001 (FIXED), VF-NEW-002 (FIXED),
  F-NEW-156 (OBSERVED-FAIL), R-NEW-402 (instrument, IMPLEMENTED).
- APP_MATRIX.md: S81 §35 columns added via the generator (VISUAL_STATUS,
  COLOR_SCORE, IMAGE_SCORE, GRAPHICS_FLAGS, MISSING_APIS) + 7 §39
  DOWNGRADES recorded. Generator fixed, never hand-patched (§24).
- GitHub issue #24: consolidated S81 tracking issue in the §28/§29 evidence
  format.

## 8. Final regression (§0 gate)

battery 26/26 rc=0 · fidelity BYTE-IDENTICAL 90/90 · f152 6/6 · f153 3/3 ·
pixel-golden spot verifier 4/4 (f024/f026/f028/f030 end-to-end).

## 9. Honest completion statement (§51)

CORPUS_READY · EXECUTION_PARTIAL. 200 items indexed with provenance;
25 executed in BATCH-01; the curated ladder re-audited and downgraded
honestly; 2 visual failures root-caused-fixed with regression proofs.
NOT claimed: "200_APPS_VERIFIED", any L4/L5 status, any fixture-as-real-APK
substitution. P9/TimeLimit execution + BATCH-02..04 + the onCreate-unwind
family are the queued next wave.
