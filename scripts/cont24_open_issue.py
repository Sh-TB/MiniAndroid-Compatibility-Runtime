#!/usr/bin/env python3
"""CONT-24 — open the SKEL-LIGHT impact Issue (measurement only, no main-line change)."""
import subprocess, json, sys

def token():
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no github credential")

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

TITLE = "[CONT-24 EXPERIMENT — measurement only] Skeleton-Light: one 490-line generic skeleton painter vs ~10.6K lines of graphics machinery — measured impact"

BODY = """## What this is (and is not)

Per the wave directive, this is a **measurement-only experiment**: "instead of emulating the graphics stack piece by piece, fully simulate ONE generic skeleton-light — by adding one skeleton-light, thousands of lines for graphics and roots and others were deleted. Test it ONLY as a test; if it has impact, explain the measured impact here. Do not change our main line."

- **No main-line change.** Everything lives on the branch `cont24/skeleton-light-experiment` (commit 12bd2a39), behind `MINIANDROID_SKELETON_LIGHT=1` (default OFF, proven byte-inert).
- The user's "thousands of lines deleted" claim was **confirmed quantitatively for the frame-production role** — and the costs were measured too. Full evidence: `evidence/cont24/SKEL_LIGHT_EXPERIMENT.md`, runs `run/cont24/`.

## 1. What was built

| item | size |
|---|---|
| `miniandroid/src/renderer/skeleton_light.{h,cpp}` — ONE self-contained painter: compact measure (MATCH_PARENT/WRAP_CONTENT/margins/orientation) + paint (real `bg_color` fills, 5×7 ASCII texts, depth-cycled outlines, image placeholders, clickable ticks, GONE/INVISIBLE) | **490 lines** |
| env-gated hook in `stage_render_frame_impl` (+ census mapping) | +50 lines |
| Makefile | 2 lines |

**Zero-dependency proof (link level, checkable):** `nm -u build/renderer/skeleton_light.o` → 14 undefined symbols = C++ runtime + `getenv` + `roundf` + `std::string::find` + `ViewShadow::find_node`. **No reference at all** to canvas_shadow, text_shaper, bitmap_font_data, vector_decode, gif_decoder, bitmap_shadow, state_list.

**Inertness sanity:** gate OFF on the experiment binary → anchors byte-identical (dooz `d602648e8e401895`, opencalc `a976d2f9fb675cb3`).

## 2. The "thousands of lines" arithmetic (the user's claim, measured)

For the **classic-canvas frame family**, machinery the skeleton path does not execute:

| file | lines |
|---|---|
| engine draw walk (`execution_engine.cpp` 2903–5162) | ~2,140 of 2,260 |
| `canvas_shadow.cpp` (Canvas-op emulation) | 2,261 |
| `text_shaper.cpp` (HarfBuzz/FreeType/FriBidi) | 1,166 |
| `bitmap_font_data.h` | 2,028 (skeleton: 672-byte 5×7 font) |
| `software_renderer.cpp` | ~1,284 of 1,434 |
| `vector_decode.cpp` | 949 |
| `bitmap_shadow.cpp` (paint decode) | 604 |
| `state_list.cpp` | 176 |
| **total** | **~10.6K lines** |

→ **490 lines replace the role of ~10.6K lines for producing an informative frame of a View-family app.** Scope honesty: this is the *frame-production role* — the same files still serve DEX-side Canvas calls, measure, and app-logic APIs, so they are not wholesale-deletable from the repo.

Registry cross-check: **255 of 586 roots (43.5%) are graphics-labeled**; 105 of them ROOT-CAUSED-FIXED — a large share of past root work exists because of the per-op graphics emulation whose frame role the skeleton covers.

## 3. A/B battery — 11 targets (canonical sweep, 5 frames / 15 s)

| target | family | base → skel colors | verdict |
|---|---|---|---|
| dooz | Compose | 1 (blank) → 2 | structure hint; **rc flip 1→0 = verdict inflation (§4)** |
| telegram | complex | 1 (blank) → 2 | **first non-blank pixels at this protocol** (structure only) |
| ballbreak | Canvas game | 1 (blank) → 2 | structure hint |
| opencalc | View | 217 → 4 | structure visible; fidelity LOSS |
| unote | View | 128 → 6 | fidelity loss, structure ok |
| microtimer | View | 120 → 7 | fidelity loss, structure ok |
| gmdice | View game | 187 → 7 | fidelity loss, structure ok |
| tictactoe | View game | 364 → 5 | full-coverage structure (2.09M px) |
| notes | AppCompat | 65 → 2 | wash (baseline flat) |
| **flappycow** | Surface/GL game | **507 (SUCCESS) → 1 (blank, rc 1)** | **REGRESSION — skeleton replaced the surface composite** |
| stopwatch | View | 1 (blank) → 1 (unchanged) | tree absent at frame time → skeleton cannot help |

Determinism ×3: dooz `4163ee86125d52c0`, tictactoe `4bce76f0a58269a7`, telegram `e88f290b3550711a` — byte-identical. Telegram/notes/ballbreak skel frames are byte-identical to each other: the "generic minimum frame" is target-independent.

## 4. The hazards (measured, not hypothetical)

1. **Verdict inflation — proven.** dooz flipped rc 1→0 (`Status: SUCCESS`) because painting the ComposeView *wrapper outline* set `app_draw_ops>0` → REAL_APP_CONTENT proof. That is the FRAMEWORK_CHROME_ONLY ≠ REAL_APP_CONTENT violation. A production skeleton needs its own verdict class (`SKELETON_STRUCTURE_ONLY`), strictly weaker.
2. **Surface-family destruction — proven.** flappycow 507-color SUCCESS → blank + rc 1. Family routing is mandatory; a global paint hook must never replace the GL/surface composite.
3. **Fidelity loss — proven.** Every rich render collapses to structure; non-ASCII text (opencalc ×6) becomes placeholder bars.
4. **No help where the tree is absent** (stopwatch). The skeleton cannot invent a tree.
5. **Log masking.** opencalc "uncaught" grep hits 9→3: the same 2 exception roots simply stop repeating per frame when the draw walk is skipped. Fewer log lines ≠ fewer defects.

## 5. Verdict — where the idea helps, where it cannot

**Wins:** (a) the machinery arithmetic (490 vs ~10.6K, link-proven); (b) first pixels on baseline-blank View-family faces + structure on the Compose blank; (c) a deterministic generic minimum frame = a cheap corpus-wide smoke-test instrument; (d) a fallback frame class for future wave evidence when the real pipeline is blocked.

**Cannot win:** Compose *content* (dooz's real blocker is F-NEW-277 recomposition starvation — composition, not paint), surfaces/games (must keep compositing), glyph fidelity, absent trees.

**Bottom line:** a legitimate **diagnostic + fallback layer with its own verdict class**, not a main-line replacement. The main line stays source-first.

## 6. Bonus finding + unapplied-achievements inventory

- **Stale asset:** `view_renderer.cpp` (684 LOC, UNIFIED_007 era) **no longer compiles** against the current ViewShadow API — discovered when reusing it was attempted; it is itself a scattered achievement (recommend: delete or repair as the shared measure pass).
- Inventory pushed as `evidence/cont24/UNAPPLIED_ACHIEVEMENTS.md`: **16 RESEARCHED-NOT-IMPLEMENTED** rows (12 of them one generic jni_bridge classification law — highest single-law ROI), **110 PARTIAL**, **72 UNPROVEN**, the reverted CONT-23 lifecycle patch (probe locked 5/5), the CONT-12 real-Compose oracle (test-only, proved F-NEW-266), and the 10,258-LOC deleted experiment chain (f9f3013d).

## 7. Reproduce

```bash
git checkout cont24/skeleton-light-experiment
cd miniandroid && timeout 570 make -j1 BUILD_DIR=build     # 614677b60931b94f
bash scripts/cont24_battery.sh run/cont24/bin/miniandroid_baseline_fa88902f run/cont24/base base
bash scripts/cont24_battery.sh miniandroid/build/miniandroid run/cont24/skel skel
```

*Labels: experiment, measurement-only, no-main-line-change.*
"""

def main():
    tok = token()
    body = json.dumps({"title": TITLE, "body": BODY,
                       "labels": ["experiment", "measurement-only"]})
    out = subprocess.run(
        ["curl", "-sS", "-X", "POST",
         f"https://api.github.com/repos/{REPO}/issues",
         "-H", f"Authorization: token {tok}",
         "-H", "Accept: application/vnd.github+json",
         "-d", body], capture_output=True, text=True)
    r = json.loads(out.stdout)
    if "number" in r:
        print(f"ISSUE CREATED #{r['number']}: {r['html_url']}")
    else:
        print("ERROR:", out.stdout[:800]); sys.exit(1)

if __name__ == "__main__":
    main()
