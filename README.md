# MiniAndroid — a from-scratch Android APK Compatibility Runtime

<p align="center">
  <img src="docs/assets/miniandroid-silkie-mascot.png" width="132" alt="MiniAndroid mascot — a fluffy Silkie hen (decorative only)">
</p>
<p align="center"><sub>Decorative project mascot — a Silkie hen. Not an Android/Google mark; carries no claim.</sub></p>

**Repository:** https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime (original project, not a fork) · **License:** MIT · **Current wave:** S87 (source-first near-blank strike — F-NEW-171..174 fixed: secuso dame/2048 + mykanji/no.thanks now inflate real UI; full achievement audit + evidence census)

---

## 🎮 Flagship proof — real APKs playing on MiniAndroid (user-requested showcase)

Both GIFs below are **captured from real APK execution on the MiniAndroid
runtime** — the engine parsed the DEX bytecode, drove the app's own Activity
lifecycle and View tree, dispatched real click events, and rasterized every
pixel you see. The snake chases the apple, dies, restarts; the 2048 tiles
slide and merge on real `View.onDraw` output — no emulator, no video player,
no faked frames (SHA256-pinned in
[canonical/SHA256SUMS](docs/evidence/canonical/SHA256SUMS)).

| Snake Deluxe — full gameplay loop (49 frames) | 2048 — tile merges to SCORE 200 (65 frames) |
|---|---|
| <img src="docs/evidence/canonical/com.miniandroid.snakedeluxe.gif" width="260" alt="Snake Deluxe gameplay GIF — real APK on MiniAndroid"> | <img src="docs/evidence/canonical/com.miniandroid.g2048.gif" width="260" alt="2048 gameplay GIF — real APK on MiniAndroid"> |
| `LOADED → LAUNCHED → RENDERED → INTERACTED → STATE_CHANGED` · L3 | `LOADED → LAUNCHED → RENDERED → INTERACTED → STATE_CHANGED` · L2 |

*These two titles anchor the in-house game family —
[TicTacToe Deluxe (دوز)](docs/evidence/canonical/com.miniandroid.tictactoedeluxe.gif)
and [Mini Tetris](docs/evidence/canonical/com.miniandroid.tetris.gif) are
proven the same way (full matrix: 96 records in
[docs/ACHIEVEMENTS.md](docs/ACHIEVEMENTS.md)).*

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
| Titles executed & recorded | **148** (87 games · 60 apps · 1 fixture) |
| Added in S86 (this wave) | **MiniCraft (خانه سازی)** — 5th in-house game — + Dodge promoted to full gameplay; 7 engine laws F-NEW-164..170 (SurfaceView surface chain) all A/B-proven |
| Added in S87 (this wave) | **4 A/B-proven engine laws F-NEW-171..174** (APXACT depth underflow, FragmentActivity super-chain, ViewConfiguration object, beneath finisher) — the near-blank family root-cause cluster; 10-title source-first probe corpus (upstream repos fetched and read before execution); full evidence audit (511 images, 36 canonical artifacts SHA-verified 36/36, zero executed-but-unrecorded) |
| VERIFIED (launched + rendered, content-verified UI) | **22** |
| VERIFIED-INTERACTIVE (real click → state change, GIF) | **12** |
| PARTIAL (rendered with root-caused divergences) | 2 |
| OBSERVED (loaded/ran; near-blank shell class — text records, never shipped as images) | 112 |
| BLOCKED | 0 |
| Titles with real rendered UI pixels (L2+) | 51 |
| Canonical screenshots (ONE per title) | 36 (12 GIF + 24 JPG) |

**S85 evidence-integrity hardening (EVID-CLASS-S85):** the visual gate now
rejects the engine-default shell class (white framebuffer + black status
region, `eb16ab5c…`) that previously slipped through L2 via status-bar
pixels. **72 records were honestly demoted to OBSERVED** this wave —
the numbers above are the content-verified residue, not inflation.

Regression gates at this HEAD: **battery 26/26 · golden graphics ladder
10/10 · S83-B2 ladder 2/2** (F-NEW-163 A/B-verified, zero regressions).

## Hero titles (full matrix: 147 records in [docs/ACHIEVEMENTS.md](docs/ACHIEVEMENTS.md))

| Title | Type | Source | Status | Level | State change | Canonical |
|---|---|---|---|---|---|---|
| **Snake Deluxe** | game | in-house (games/snake-deluxe) | VERIFIED-INTERACTIVE | L3 | ✅ | [com.miniandroid.snakedeluxe.gif](docs/evidence/canonical/com.miniandroid.snakedeluxe.gif) |
| **2048** | game | in-house (games/2048) | VERIFIED-INTERACTIVE | L2 | ✅ | [com.miniandroid.g2048.gif](docs/evidence/canonical/com.miniandroid.g2048.gif) |
| **TicTacToe Deluxe (دوز)** | game | in-house (games/tictactoe-deluxe) | VERIFIED-INTERACTIVE | L3 | ✅ | [com.miniandroid.tictactoedeluxe.gif](docs/evidence/canonical/com.miniandroid.tictactoedeluxe.gif) |
| **MiniCraft (خانه سازی)** | game | in-house (games/minicraft) | VERIFIED-INTERACTIVE | L3 | ✅ | [com.miniandroid.minicraft.gif](docs/evidence/canonical/com.miniandroid.minicraft.gif) |
| **Mini Tetris** | game | in-house (games/mini-tetris) | VERIFIED-INTERACTIVE | L3 | ✅ | [com.miniandroid.tetris.gif](docs/evidence/canonical/com.miniandroid.tetris.gif) |
| **Vector Pinball (bouncy)** | game | [src](https://github.com/dozingcatsoftware/Bouncy) | VERIFIED-INTERACTIVE | L2 | ✅ S85 | [com.dozingcatsoftware.bouncy.gif](docs/evidence/canonical/com.dozingcatsoftware.bouncy.gif) |
| **URLChecker** | app | [src](https://github.com/TrianguloY/URLChecker) | VERIFIED-INTERACTIVE | L2 | ✅ S85 | [com.trianguloy.urlchecker.gif](docs/evidence/canonical/com.trianguloy.urlchecker.gif) |
| **TicTacToe Classic** | game | F-Droid com.emmanuelmess.tictactoe | VERIFIED-INTERACTIVE | L2 | ✅ | [com.emmanuelmess.tictactoe.gif](docs/evidence/canonical/com.emmanuelmess.tictactoe.gif) |
| **Dodge** (SurfaceView, fully playable) | game | [src](https://github.com/dozingcat/dodge-android) | VERIFIED-INTERACTIVE | L3 | ✅ | [com.dozingcatsoftware.dodge.gif](docs/evidence/canonical/com.dozingcatsoftware.dodge.gif) |
| **SolitaireCG** | game | F-Droid net.sourceforge.solitaire_cg | VERIFIED | L2 | — | text record |
| **Mines 3D** | game | F-Droid cos.premy.mines | VERIFIED | L2 | — | [cos.premy.mines.jpg](docs/evidence/canonical/cos.premy.mines.jpg) |
| **Telegram** | app | [official APK](https://telegram.org/dl/android/apk) | OBSERVED (reviewed S85) | L1 | — | text record |
| **Dooz (دوز, F-Droid)** | game | F-Droid io.github.yamin8000.dooz | OBSERVED (compose frontier) | L1 | — | text record |

**In-house games built for the runtime** (source in [`games/`](games/)):
Snake Deluxe · Mini Tetris · 2048 · TicTacToe Deluxe (دوز) · MiniCraft
(خانه سازی) — each proven with full interaction loops (chase → death →
restart; X → AI → O-win → round persistence; terrain → build → house).

**S86 graphics strike (upstream-source-driven):** the Dodge question —
"why does the GIF only show two colors?" — was root-caused by reading the
actual upstream code: `FieldView extends SurfaceView` and paints through
`SurfaceHolder.lockCanvas` from a game thread. Seven engine laws
(F-NEW-164 SurfaceView surface chain, F-NEW-165 Deque family, F-NEW-166
Display family, F-NEW-167 getPreferences, F-NEW-168 INVISIBLE-subtree
draw law, F-NEW-169 RectF-object drawRect, F-NEW-170 getWidth/getHeight)
now make the real game render: black field, red/green goal zones, blue
dodger, moving bullet swarm — all A/B-proven with battery 26/26 + golden
ladder 10/10. Impact audit across all levels:
[LEVEL_IMPACT_S86.md](docs/evidence/LEVEL_IMPACT_S86.md).

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

- **Near-blank shell class** (114 OBSERVED titles): apps whose engine runs
  (launch, lifecycle, resources, sometimes full static init) but whose
  windows stay the engine-default white shell + black status region —
  dominated by Compose init chains (F-NEW-161, ~2/3 of modern F-Droid
  apps) and androidx adapter fallback (F-NEW-162). These are text records,
  never images.
- **GLES/libGDX/SDL titles** (F-NEW-141 family): load + launch; the
  software-GL bridge is the recorded next dependency.
- **WebView content models**: chrome renders; web content is a pinned
  frontier.
- **Non-ASCII text shaping**: ASCII pixel-proven; Persian/Arabic glyph
  runs render as zero-width (bitmap-font law) — shaping engine pending.
- **Telegram** (user-requested S85 review): launch + shell frames only;
  ImageLoader/ActionBarLayout static-init chains recorded as the current
  first divergence (multi-week native/TLS frontier).

The root-cause registry maps every one of these to the titles it blocks:
[docs/evidence/ROOT_CAUSE_REGISTRY.md](docs/evidence/ROOT_CAUSE_REGISTRY.md).

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
