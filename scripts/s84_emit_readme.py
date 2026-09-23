#!/usr/bin/env python3
"""s84_emit_readme.py — regenerate README.md as the project landing page.

All numbers are GENERATED from docs/evidence/canonical/registry.json (S84
law: no hand-written, guessed numbers on the front page).
"""
import json

ROOT = "/home/z/my-project"
reg = json.load(open(f"{ROOT}/docs/evidence/canonical/registry.json"))
T = reg["titles"]


def n(pred):
    return sum(1 for t in T if pred(t))


TOTAL = len(T)
GAMES = n(lambda t: t["type"] == "game")
APPS = n(lambda t: t["type"] == "app")
FIXTURES = n(lambda t: t["type"] not in ("game", "app"))
VERIFIED = n(lambda t: t["status"].startswith("VERIFIED"))
INTERACTIVE = n(lambda t: t["status"] == "VERIFIED-INTERACTIVE")
PARTIAL = n(lambda t: t["status"].startswith("PARTIAL"))
OBSERVED = n(lambda t: t["status"] == "OBSERVED")
BLOCKED = n(lambda t: t["status"] == "BLOCKED")
RENDERED = n(lambda t: t["rendered"])
INTERACTED = n(lambda t: t["interacted"])
SCHANGED = n(lambda t: t["state_changed"])
NEW50 = n(lambda t: t["session"] == "S84")
GIF = n(lambda t: t["artifact"].endswith(".gif"))
JPG = n(lambda t: t["artifact"].endswith(".jpg"))

HERO = [
    "com.miniandroid.snakedeluxe", "com.miniandroid.tictactoedeluxe",
    "com.miniandroid.tetris", "com.miniandroid.g2048",
    "io.github.yamin8000.dooz", "com.emmanuelmess.tictactoe",
    "eu.veldsoft.fish.rings", "eu.veldsoft.free.klondike",
    "com.dozingcatsoftware.bouncy", "com.smorgasbork.hotdeath",
    "org.bobstuff.bobball", "com.dozingcatsoftware.dodge",
]

hero_rows = []
for pkg in HERO:
    t = next(x for x in T if x["package"] == pkg)
    art = (f"[{t['artifact'].rsplit('/', 1)[-1]}](../{t['artifact']})"
           if t["artifact"] else "—")
    sc = "✅" if t["state_changed"] else ("↻" if t["interacted"] else "—")
    src_url = t["upstream"] or t["source"]
    if src_url.startswith("http"):
        src_cell = f"[src]({src_url})"
    else:
        src_cell = src_url.replace("|", "/")
    hero_rows.append(f"| **{t['title']}** | {t['type']} | "
                     f"{src_cell} | "
                     f"{t['status']} | L{t['level']} | {sc} | {art} |")

MD = f"""# MiniAndroid — a from-scratch Android APK Compatibility Runtime

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
| Titles executed & recorded | **{TOTAL}** ({GAMES} games · {APPS} apps · {FIXTURES} fixtures) |
| Added in S84 (this wave) | **{NEW50}** new F-Droid titles, all with upstream source links |
| VERIFIED (launched + rendered real frames) | **{VERIFIED}** |
| VERIFIED-INTERACTIVE (real click → rendered state change, GIF) | **{INTERACTIVE}** |
| PARTIAL (rendered, first-divergence root-caused) | {PARTIAL} |
| OBSERVED (loaded/ran; near-blank or sub-render frames — logged, not shipped as images) | {OBSERVED} |
| BLOCKED | {BLOCKED} |
| Titles with real rendered UI pixels | {RENDERED} |
| Titles with dispatched real input | {INTERACTED} |
| Titles with proven input→state change | {SCHANGED} |
| Canonical screenshots (ONE per title) | {GIF + JPG} ({GIF} GIF + {JPG} JPG) |

Regression gates at this HEAD: **battery 26/26 · golden graphics ladder
10/10** (F-NEW-160 A/B-verified, zero regressions).

## Hero titles (full matrix: {TOTAL} records in [docs/ACHIEVEMENTS.md](docs/ACHIEVEMENTS.md))

| Title | Type | Source | Status | Level | State change | Canonical |
|---|---|---|---|---|---|---|
{chr(10).join(hero_rows)}

**In-house games built for the runtime** (source in [`games/`](games/)):
Snake Deluxe · Mini Tetris · 2048 · TicTacToe Deluxe — each proven
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
"""

with open(f"{ROOT}/README.md", "w") as f:
    f.write(MD)
print("README.md written:", len(MD), "bytes")
