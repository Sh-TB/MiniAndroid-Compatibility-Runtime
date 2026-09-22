# MiniAndroid — a from-scratch Android APK Compatibility Runtime

<p align="center">
  <img src="docs/assets/miniandroid-silkie-mascot.png" width="132" alt="MiniAndroid mascot — a fluffy Silkie hen (decorative only)">
</p>
<p align="center"><sub>Decorative project mascot — a Silkie hen. Not an Android/Google mark; carries no claim.</sub></p>

**Repository:** https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime (original project, not a fork) · **License:** MIT · **Current wave:** S84 (canonical achievements + 50 new titles)

---

## What MiniAndroid is (and is not)

**MiniAndroid is** a from-scratch C++17 compatibility runtime that executes
**real Android APKs** — parsing DEX bytecode, ARSC resources and AXML
layouts, then driving the app's own Activity lifecycle, View tree, click
handlers and Canvas rendering to a real pixel framebuffer captured as
screenshots. Every claim in this repository is pinned to committed,
SHA256-tracked evidence; nothing is asserted from a `rc=0` alone.

**MiniAndroid is not** an emulator or a kernel-level Android: there is no
Linux kernel, no ART/Dalvik binary, no GPU — rendering is a deterministic
software raster pipeline, and app logic runs through a re-implemented
Dalvik-class interpreter. Compose/Flutter/GLES-heavy apps still hit
honestly-recorded frontiers (see root-cause registry below).

## Current progress (generated from the canonical registry — not hand-written)

| Metric | Value |
|---|---|
| Titles executed & recorded | **96** (61 games · 34 apps · 1 fixtures) |
| Added in S84 (this wave) | **50** new F-Droid titles, all with upstream source links |
| VERIFIED (launched + rendered real frames) | **29** |
| VERIFIED-INTERACTIVE (real click → rendered state change, GIF) | **9** |
| PARTIAL (rendered, first-divergence root-caused) | 3 |
| OBSERVED (loaded/ran; near-blank or sub-render frames — logged, not shipped as images) | 63 |
| BLOCKED | 1 |
| Titles with real rendered UI pixels | 68 |
| Titles with dispatched real input | 11 |
| Titles with proven input→state change | 9 |
| Canonical screenshots (ONE per title) | 32 (9 GIF + 23 JPG) |

Regression gates at this HEAD: **battery 26/26 · golden graphics ladder
10/10** (F-NEW-160 A/B-verified, zero regressions).

## Hero titles (full matrix: 96 records in [docs/ACHIEVEMENTS.md](docs/ACHIEVEMENTS.md))

| Title | Type | Source | Status | Level | State change | Canonical |
|---|---|---|---|---|---|---|
| **Snake Deluxe** | game | in-house (games/snake-deluxe) | VERIFIED-INTERACTIVE | L3 | ✅ | [com.miniandroid.snakedeluxe.gif](../docs/evidence/canonical/com.miniandroid.snakedeluxe.gif) |
| **TicTacToe Deluxe (دوز)** | game | in-house (games/tictactoe-deluxe) | VERIFIED-INTERACTIVE | L3 | ✅ | [com.miniandroid.tictactoedeluxe.gif](../docs/evidence/canonical/com.miniandroid.tictactoedeluxe.gif) |
| **Mini Tetris** | game | in-house (games/mini-tetris) | VERIFIED-INTERACTIVE | L3 | ✅ | [com.miniandroid.tetris.gif](../docs/evidence/canonical/com.miniandroid.tetris.gif) |
| **2048** | game | in-house (games/2048) | VERIFIED-INTERACTIVE | L2 | ✅ | [com.miniandroid.g2048.gif](../docs/evidence/canonical/com.miniandroid.g2048.gif) |
| **Dooz (tic-tac-toe)** | game | F-Droid io.github.yamin8000.dooz | VERIFIED | L2 | — | [io.github.yamin8000.dooz.jpg](../docs/evidence/canonical/io.github.yamin8000.dooz.jpg) |
| **TicTacToe Classic** | game | F-Droid com.emmanuelmess.tictactoe | VERIFIED-INTERACTIVE | L2 | ✅ | [com.emmanuelmess.tictactoe.gif](../docs/evidence/canonical/com.emmanuelmess.tictactoe.gif) |
| **Fish Rings** | game | [src](https://github.com/VelbazhdSoftwareLLC/FishRingsForAndroid) | VERIFIED | L10 | — | [eu.veldsoft.fish.rings.jpg](../docs/evidence/canonical/eu.veldsoft.fish.rings.jpg) |
| **FreeKlondike** | game | [src](https://github.com/VelbazhdSoftwareLLC/FreeKlondike) | VERIFIED | L10 | — | [eu.veldsoft.free.klondike.jpg](../docs/evidence/canonical/eu.veldsoft.free.klondike.jpg) |
| **Vector Pinball (bouncy)** | game | [src](https://github.com/dozingcatsoftware/Bouncy) | VERIFIED | L5 | — | [com.dozingcatsoftware.bouncy.jpg](../docs/evidence/canonical/com.dozingcatsoftware.bouncy.jpg) |
| **com.smorgasbork.hotdeath** | game | [src](https://github.com/jpriebe/hotdeath) | VERIFIED-INTERACTIVE | L2 | ✅ | [com.smorgasbork.hotdeath.gif](../docs/evidence/canonical/com.smorgasbork.hotdeath.gif) |
| **org.bobstuff.bobball** | game | [src](https://github.com/bobthekingofegypt/BobBall) | VERIFIED-INTERACTIVE | L2 | ✅ | [org.bobstuff.bobball.gif](../docs/evidence/canonical/org.bobstuff.bobball.gif) |
| **com.dozingcatsoftware.dodge** | game | [src](https://github.com/dozingcat/dodge-android) | VERIFIED-INTERACTIVE | L2 | ✅ | [com.dozingcatsoftware.dodge.gif](../docs/evidence/canonical/com.dozingcatsoftware.dodge.gif) |

**In-house games built for the runtime** (source in [`games/`](games/)):
Snake Deluxe · Mini Tetris · 2048 · TicTacToe Deluxe (دوز) — each proven
with full autoplay interaction loops (chase → death → restart; X → AI →
O-win → round persistence).

## Where everything lives

1. **What each title proved / what remains** → [docs/ACHIEVEMENTS.md](docs/ACHIEVEMENTS.md)
   — ONE record per title (S84 canonical law).
2. **Canonical screenshots** → [`docs/evidence/canonical/`](docs/evidence/canonical/)
   + machine index [docs/evidence/CANONICAL_SCREENSHOTS.md](docs/evidence/CANONICAL_SCREENSHOTS.md).
3. **Source links** — every record carries the original project's URL
   (F-Droid page + upstream repo). Chain per title:
   `Title → Source → APK+SHA → Execution session → Achievement → ONE screenshot → root cause`.
4. **What still fails and why** → [docs/evidence/ROOT_CAUSE_REGISTRY.md](docs/evidence/ROOT_CAUSE_REGISTRY.md)
   — every blocked/partial title references a shared root-cause ID
   (one family = one issue, not 50 duplicate investigations).
5. **Reproduce any run** → `./miniandroid/build/miniandroid run --execution-mode real-dalvik --frames 8 --frame-delay 300 -o <dir> <apk>`
   at the recorded commit; gates: `bash scripts/s77_baseline_battery.sh`.
6. **Validate the evidence chain** → `python3 tools/verify_canonical_evidence.py`
   (12 checks: unique per title, SHA match, no orphans/duplicates,
   provenance present, visual claims require artifacts).

## Evidence policy (S84, binding)

> **One title → one canonical screenshot.** Interactive titles get ONE
> gameplay GIF. No screenshot is copied across reports/issues — every
> document links to the same canonical artifact. Near-blank frames are
> never visual evidence (S54 gate law): they are recorded as text with
> log references. Debugging frame-dumps from closed investigations were
> removed (345 MB) — git history retains everything, and
> [S84_CLEANUP_MANIFEST.json](docs/evidence/S84_CLEANUP_MANIFEST.json)
> records every deletion by SHA256.

## What MiniAndroid is NOT (yet) — honest frontiers

- **Compose UI internals** (F-NEW-161, ~2/3 of modern F-Droid apps hit
  this): static compose UI renders; dynamic recomposition machinery is
  not implemented.
- **GLES/libGDX/SDL titles** (F-NEW-141 family): load + launch; the
  software-GL bridge is the recorded next dependency.
- **WebView content models**: chrome renders; web content is a pinned
  frontier.
- **Non-ASCII text shaping**: ASCII pixel-proven; Persian/Arabic glyph
  runs render as zero-width (bitmap-font law) — shaping engine pending.

The root-cause registry maps every one of these to the titles it blocks.

## Project discipline

- **Honesty gate:** the screenshot quality gate has *downgraded* claims
  repeatedly (S53–S54 era) — blank/near-blank frames are never presented
  as success, and S84's validator caught a 16-title byte-identical
  evidence class from S83 that is now demoted to OBSERVED.
- **Master audit:** [docs/audit/MASTER_CHECKLIST.md](docs/audit/MASTER_CHECKLIST.md)
  — every constitution rule, campaign and gap as individual auditable rows.
- **Battery:** `bash scripts/s77_baseline_battery.sh` → 26/26 at HEAD;
  golden ladder 10/10; every engine law lands only with A/B proof and
  zero regressions.
