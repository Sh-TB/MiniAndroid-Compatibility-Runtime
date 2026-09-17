# S53 Image & Artifact Census — Screenshot Quality Gate Enforcement

Date: 2026-09-17 · HEAD before: `ef569eda` (S52) · Gate: `scripts/s53_frame_gate.py`,
census: `scripts/s53_image_census.py`, hygiene executor: `scripts/s53_image_hygiene.py`

## Why

The S53 law (no fake success, no white/black frames as achievements) was applied
**retroactively to the whole tree**, not only to new runs. A full quality census of
every tracked image (luminance distribution, near-white/near-black ratio, color
count, byte-identity) found systematic blank-frame and duplicate pollution.

## Census result (tracked images)

| Metric | Before | After | Δ |
|---|---|---|---|
| Tracked images | 591 | 89 | **−502** |
| Unique (by SHA256) | 151 | 83 | −68 |
| Blank-class (≥99.5% single-tone or ≤8 colors) | 431 | 19* | −412 |
| Byte-identical duplicates | 440 | 6* | −434 |

\* remaining 19 flagged = **legitimate golden oracles / APK resource fixtures**
(`helloworld_golden`, `external_hello_golden`, `golden03`, `density_matrix`
drawable icons, `hello_art.png` fixture resource, era ledger renders). Remaining
6 duplicates = intentional determinism proofs (`hello_color_golden/retest_run1..3`
identical frames are the 3-run determinism evidence itself) and differently-named
roles of the same golden inside cited evidence docs.

## Fraud-class findings that triggered this purge

1. **7 "different app" screenshots in the S51 gallery were the same file**:
   `s51_audit/{itsfrz,openlauncher,rttt,secuso_dicer,simplekeyboard,stopwatchmuellerma}.jpg`
   + `apps_ledger` members were byte-identical 3632 B entry-class blank frames.
   (The canonical file disclosed the shared-SHA classes, but storing N copies
   added zero evidence — now text-only records.)
2. **Chess Clock "SUCCESS full render" was a black frame**: gate shows 99.3 %
   near-black, **2 colors total** (`e4a2d7c9…`). Click-test 2026-09-17: 4 clickable
   views, **0/8 state changes**. `--tap` delta exists (5,564 px → `93c3121c…`)
   but is sub-perceptual on a black field. Verdict downgraded to **RENDER_ONLY**
   (see EXECUTION_ACHIEVEMENTS §3.1).
3. **Notes (billthefarmer) "SUCCESS" was a near-white frame**: 99.1 % near-white,
   5 colors, 0/3 click state changes → **RENDER_ONLY**.
4. **An entire "solved" gallery was 100 % white empty frames**:
   `docs/evidence/solved/gpg_092_095_session/root_gpg/gpg_f092..f101/screenshot.png`
   — every file 10802 B, 3 colors, 100 % near-white (123 copies of one blank
   propagated across campaign dirs).
5. **17 zero-byte images** were tracked (e.g. `campaign014/bouncy/screenshot.png`).
6. **440 byte-identical duplicates** — run outputs copied into 2–15 campaign dirs
   each (one dooz blank had **84 copies**, one gpg blank **123 copies**).
7. **549 generated files under `miniandroid/run/`** (212 run dirs: report.md,
   screenshots, frames) were tracked — runtime output is LOCAL-ONLY by policy.

## Removal classes executed (history NOT rewritten; blobs remain in git history)

| Class | Files | Provenance record |
|---|---|---|
| blank-class evidence images | 64+6 | `S53_REMOVED_IMAGES_SHA256SUMS.txt` |
| byte-identical duplicates | 434 | same |
| zero-byte images | 17 | same |
| generated `miniandroid/run/**` (incl. images) | 549 paths (272 unique after cross-list dedup) | `S53_REMOVED_RUNDIR_SHA256SUMS.txt` |

Every removed file is recorded as `SHA256-16  size  reason  path`. Git history
retains all blobs; nothing was rewritten.

## Canonical gallery (replaces all per-campaign galleries)

`docs/evidence/s53_frames/` — 9 JPGs ≤100 KB, quality-gated
(`near-white/near-black/colors` recorded per file in `SHA256SUMS`), indexed with
milestone + SHA + why-it-matters in `docs/EXECUTION_ACHIEVEMENTS.md` §4:

- `gmdice_base/after` — real dice UI → post-input roll **"14 · 15 · 15"**
- `microtimer_base/after` — keypad UI → click makes **"00:00:00"** timer display appear
- `simplestopwatch_base/after` — Start/Delay → **Stop/Lap** (running state)
- `headingcalculator_base/after` — full keypad UI → digit input changes display
- `unote_base` — real notes-list UI (Add note / Search / Quit)

Blank frames are **never stored**: chessclock + notes are recorded as
`blank-frame observed` text entries with gate numbers and SHAs.
