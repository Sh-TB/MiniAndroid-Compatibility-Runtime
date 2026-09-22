#!/usr/bin/env python3
"""S82-GFX-REVOLUTION P6 — canonical outputs.

1. GRAPHICS_GAP_MATRIX.json (docs/audit) — per-executed-title chain bits +
   families + root causes (complements App Matrix, no duplication).
2. Registers F-NEW-158 (FIXED) + F-NEW-159 (OPEN, null framework receivers)
   in docs/corpus/s82/root_cause_graph.{json,md} and the S82 compatibility
   index ROOT_CAUSES.
3. Honest fanout updates: GAME-004 palette delta recorded.
4. Builds docs/knowledge/graphics/{GRAPHICS_PIPELINE,GRAPHICS_ROOT_CAUSES,
   PIXEL_PROVENANCE,GRAPHICS_FIX_FANOUT}.md — upgrade-in-place targets if
   canonical equivalents already exist (none do; verified by ls).
"""
import hashlib
import glob
import json
import os
import subprocess
from collections import Counter

ROOT = "/home/z/my-project"
GDIR = f"{ROOT}/docs/knowledge/graphics"
AUD = f"{ROOT}/docs/audit"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()[:12]


def main():
    index = json.load(open(f"{ROOT}/docs/corpus/s82/compatibility_index.json"))
    fams = json.load(open(f"{ROOT}/docs/corpus/s82/graphics_families.json"))
    fam_by_pkg = {e["PACKAGE"]: e for e in fams.get("TITLES", []) if e.get("PACKAGE")}
    fanout = json.load(open(f"{ROOT}/run/s82gfx/fanout/FANOUT_RESULT.json"))
    verdicts = json.load(open(f"{ROOT}/run/s82gfx/LADDER_VERDICT.json"))

    # ---- 1. Graphics Gap Matrix ------------------------------------------
    matrix = {
        "WAVE": "S82-GFX-REVOLUTION",
        "HEAD_AT_GENERATION": git_head(),
        "LAW": ("DECODED != RENDERED; RENDERED != GRAPHICALLY_CORRECT; "
                "launch success != visual success"),
        "FIXTURE_LADDER": {k: {"PASS": v.get("PASS"),
                               "shot_nonwhite": (v.get("chain") or {})
                                                    .get("shot", {})
                                                    .get("nonwhite_px"),
                               "shot_unique": (v.get("chain") or {})
                                                  .get("shot", {})
                                                  .get("unique_colors")}
                            for k, v in verdicts.items()},
        "TITLES": [],
        "SUMMARY": {},
    }
    fam_count = Counter()
    for t in index["TITLES"]:
        tid = t["TITLE_ID"]
        fp = (fam_by_pkg.get(t["PACKAGE"]) or {})
        chain = None
        if tid in fanout and isinstance(fanout[tid].get("CHAIN"), dict):
            chain = fanout[tid]["CHAIN"]
        row = {
            "TITLE": tid,
            "PACKAGE": t["PACKAGE"],
            "GRAPHICS_FAMILY": fp.get("FAMILIES", []),
            "EXECUTED": t.get("EXECUTION") == "EXECUTED",
            "STATE": t.get("STATE"),
            "ASSET_FOUND": None, "DECODED": None, "CANVAS_WRITTEN": None,
            "SCREENSHOT_CAPTURED": bool(t.get("SCREENSHOT_SHA256")),
            "VISUAL_CORRELATED": t.get("VISUAL_CORRELATION"),
            "ROOT_CAUSE": t.get("F_IDS", []) + t.get("VF_IDS", []),
            "FANOUT": None,
            "S82GFX_FANOUT_RERUN": (
                {"UNIQUE_BEFORE": (fanout[tid]["PALETTE_BEFORE_FROZEN"] or {})
                                                     .get("UNIQUE_COLORS"),
                 "UNIQUE_AFTER": (fanout[tid].get("PALETTE_AFTER_FIX") or {})
                                                     .get("UNIQUE_COLORS")}
                if tid in fanout else None),
        }
        for f in row["GRAPHICS_FAMILY"]:
            fam_count[f] += 1
        matrix["TITLES"].append(row)
    matrix["SUMMARY"] = {
        "TITLES": len(matrix["TITLES"]),
        "FAMILY_COVERAGE": len([r for r in matrix["TITLES"]
                                if r["GRAPHICS_FAMILY"]]),
        "FAMILY_COUNTS_SCANNED": fams.get("FAMILY_COUNTS"),
        "FIXTURE_LADDER_PASS": sum(1 for v in verdicts.values() if v.get("PASS")),
        "FIXTURE_LADDER_TOTAL": len(verdicts),
    }
    os.makedirs(AUD, exist_ok=True)
    json.dump(matrix, open(f"{AUD}/GRAPHICS_GAP_MATRIX.json", "w"), indent=1)

    # ---- 2. Root-cause graph updates --------------------------------------
    gpath = f"{ROOT}/docs/corpus/s82/root_cause_graph.json"
    g = json.load(open(gpath))
    g["F-NEW-158"] = {
        "title": ("PROGRAMMATIC-BACKGROUND-DROP (setBackground(Drawable)/"
                  "setBackgroundResource(resid) silently ignored; "
                  "image_resource_id clobber)"),
        "status": "ROOT_CAUSED_FIXED (S82-GFX; fixture ladder L0/L4 evidence + "
                  "regression 26/26 + pixel goldens 24/24)",
        "fanout": ["l0_solid fixture", "l4_xmldrawables fixture", "GAME-004",
                   "PROGRAMMATIC-UI titles across corpus (static families "
                   "B/C/D/E — see graphics_families.json)"],
    }
    g["F-NEW-159"] = {
        "title": ("NULL-FRAMEWORK-RECEIVER NPE family (LocaleList."
                  "toLanguageTags / WindowInsetsController."
                  "setSystemBarsAppearance on null refs → onCreate APP "
                  "BOUNDARY unwind; F-NEW-156 sub-cluster)"),
        "status": "OPEN (S82-GFX fanout probe ×2 titles re-traced: MAND-002, "
                  "APP-001 family; exact traces in run/s82gfx/fanout/*.log)",
        "fanout": ["MAND-002", "APP-001", "subset of F-NEW-156's 35"],
    }
    json.dump(g, open(gpath, "w"), indent=1)
    # md twin
    with open(gpath.replace(".json", ".md"), "w") as f:
        f.write("# S82 Root-Cause Fanout Graph\n\n")
        for k, v in g.items():
            f.write(f"## {k} — {v['title']}\n\n- status: "
                    f"{v.get('status', 'registered')}\n- fanout ({len(v.get('fanout', []))}): "
                    + ", ".join(map(str, v.get("fanout", []))) + "\n\n")

    # index ROOT_CAUSES honest update (no status inflation)
    index["ROOT_CAUSES"]["F-NEW-158"] = {
        "title": g["F-NEW-158"]["title"], "status": g["F-NEW-158"]["status"],
        "fanout_sample": ["GAME-004"],
    }
    index["ROOT_CAUSES"]["F-NEW-159"] = g["F-NEW-159"]
    # GAME-004 palette delta (executed title, honest re-run)
    for t in index["TITLES"]:
        if t["TITLE_ID"] == "GAME-004" and "GAME-004" in fanout:
            t["S82GFX_FANOUT"] = {
                "DATE": "2026-09-22",
                "NOTE": "F-NEW-158 fix re-run; palette delta only — STATE "
                        "unchanged pending full battery re-derivation",
                "UNIQUE_COLORS_BEFORE": (fanout["GAME-004"]["PALETTE_BEFORE_FROZEN"] or {}).get("UNIQUE_COLORS"),
                "UNIQUE_COLORS_AFTER": (fanout["GAME-004"].get("PALETTE_AFTER_FIX") or {}).get("UNIQUE_COLORS"),
                "EVIDENCE": "run/s82gfx/fanout/GAME-004/",
            }
    index["GENERATED"] = "2026-09-22 S82-GFX-REVOLUTION"
    json.dump(index, open(f"{ROOT}/docs/corpus/s82/compatibility_index.json", "w"),
              indent=1)

    # ---- 3. knowledge docs ------------------------------------------------
    os.makedirs(GDIR, exist_ok=True)
    head = git_head()

    with open(f"{GDIR}/GRAPHICS_PIPELINE.md", "w") as f:
        f.write(f"""# GRAPHICS PIPELINE (canonical) — S82-GFX-REVOLUTION

HEAD at writing: {head}

## The real pipeline (as implemented; single source of truth)

```
APK zip
  └─ res/ (aapt2-linked resources.arsc + binary AXML + drawables)
        │
        ├─ XML-LAYOUT path: LayoutInflater (arcs → ViewShadow tree)
        │     bg color / bg drawable / src drawable → node fields
        └─ PROGRAMMATIC path: DEX bytecode → shadow dispatch
              setBackgroundColor(I)      → ViewNode.bg_color        (CM-020)
              setBackgroundResource(I)   → ViewNode.bg_resource_id  (F-NEW-158)
              setBackground(Drawable)    → ColorDrawable map → bg_color
              setImageResource(I)        → ViewNode.image_resource_id
              BitmapFactory.decode*      → BitmapStore
              Canvas.draw*               → CanvasShadow op list

RENDER (stage_render_frame, every frame):
  window bg (theme windowBackground) → per-node tree walk:
     bg laws: state-list pick (G06 §5) > shape (F-053) > programmatic color
              > bitmap bg (F-NEW-158) > Button face fallback
     image laws: ImageView path/densities → decode_image_bytes →
                 density scale + FIT_CENTER (G04 §4/§12)
     custom views: real onDraw bytecode replay (CAMPAIGN 013)
     dialogs: rendered on top (CAMPAIGN 013 B1)
  → FrameBuffer → framebuffer_ copy → screenshot.png (+ .ppm fallback)

GL/EGL: ABSENT (F-NEW-157 family). SurfaceView/GLSurfaceView/TextureView
produce no pixels today — documented frontier, P9 is the live probe.
```

## Evidence-bit chain (§6 law) — every bit is instrumented

ASSET_FOUND → RESOURCE_RESOLVED → DECODED → BITMAP_CREATED →
VIEW_RECEIVED → DRAW_CALLED → CANVAS_WRITTEN → SURFACE_UPDATED →
COMPOSITED → SCREENSHOT_CAPTURED

Instrument: `MINIANDROID_GFX_PROVENANCE=<out.json>` (see
PIXEL_PROVENANCE.md).

## Software renderer law

Deterministic CPU framebuffer (no GPU dependency). One framebuffer, one
compositor (stage_render_frame), one capture (stage_capture_output).
libpng (color types 0/2/3/4/6 + tRNS), libjpeg, libwebp codecs behind ONE
format-detecting decoder (`decode_image_bytes`).
""")

    with open(f"{GDIR}/GRAPHICS_ROOT_CAUSES.md", "w") as f:
        f.write(f"""# GRAPHICS ROOT CAUSES (canonical) — S82-GFX-REVOLUTION

Law: FIRST DIVERGENCE ONLY — no root cause may be claimed without an
evidence-bit that went 0 (§6). Fix law: ONE ROOT CAUSE → ONE PATCH →
ONE REGRESSION → FANOUT.

## F-NEW-158 — PROGRAMMATIC-BACKGROUND-DROP  [ROOT_CAUSED_FIXED]

- **Symptom**: programmatic UIs render with default/white faces; XML
  `setBackgroundResource(R.drawable.x)` backgrounds never appear.
- **First divergence**: DRAW_CALLED=0 at background paint stage. Two
  concrete defects:
  1. `setBackground(Drawable)`/`setBackgroundDrawable(Drawable)` fell into
     the generic handled-void list — the ColorDrawable color was never
     captured.
  2. `setBackgroundResource(resid)` stored into `image_resource_id`
     (ImageView-src field) — never consulted by the background paint path
     (and clobbered an ImageView's earlier src resid).
- **Evidence**: fixture ladder l0_solid (dark ColorDrawable bg absent:
  2987 nonwhite/white-dominant) + l4_xmldrawables (shape/gradient/layer/
  selector all absent).
- **Fix**: engine-side capture (dalvik_engine) → `ViewNode.bg_resource_id`
  + ColorDrawable obj→color map; render-side resolution (ARSC select_file)
  flows into the SAME paint laws as XML backgrounds (state-list pick,
  F-053 shape, bitmap fit-draw).
- **Regression**: foundation battery 26/26 rc=0; pixel goldens 24/24 exact
  (VERIFICATION.json nonwhite); ladder 6/7 PASS after fix.
- **Fanout**: see GRAPHICS_FIX_FANOUT.md.

## F-NEW-159 — NULL-FRAMEWORK-RECEIVER NPE  [OPEN]

- **Symptom**: onCreate unwinds at APP BOUNDARY → blank/crash status.
- **Exact traces** (fanout probe re-runs, `run/s82gfx/fanout/*.log`):
  - TimeLimit MAND-002: `Lj/u;.b` → `LocaleList.toLanguageTags` on null;
    `WindowInsetsController.setSystemBarsAppearance` on null.
  - APP-001 family: same cluster.
- **Family**: sub-cluster of F-NEW-156 (onCreate APP-BOUNDARY-UNWIND, 35
  titles). Graphics fixes CANNOT reach these titles until lifecycle
  completes — execution order law (§25): F-NEW-156/159 first for them.
- **Next**: shadow the two receiver objects per AOSP semantics
  (LocaleList via Configuration; WindowInsetsController via Window),
  then regression the 35-title fanout.

## F-NEW-157 — libGDX GLSurfaceView NPE / EGL frontier  [OPEN]

- P9 hard-gate discovery (S82). Ladder l6_glsurface (plain GLSurfaceView,
  no libGDX) reproduces the family at HEAD: run "succeeds", 0 API calls,
  white screenshot (nonwhite=0, unique=1). The surface chain
  (Surface created → EGL context → swapBuffers → composition) is absent.
- Reference architectures (§14/§15): Anbox/emugl guest→host GL
  translation; SwiftShader CPU implementation law. MiniAndroid needs ONE
  deterministic software path first; software/GL backends stay separate.

## NON-ROOT-CAUSES (proven healthy — do NOT re-accuse)

- PNG decoder: color types 0/2/3/4/6 + tRNS all decode AND render
  (fixture l2, 1103 unique colors on screen).
- Density/resource selection: ARSC config picks xxhdpi-v4 correctly,
  density scale applied (fixture l3).
- ImageView resid chain: resid → select_file → decode → FIT_CENTER draw
  (fixtures l1/l2: quadrant pixels land exactly).
- Canvas clip + stroke: save/clipRect/restore honored exactly (l5 —
  initial "failure" was a fixture-authoring clip bug, i.e. the runtime
  was MORE correct than the test).
""")

    with open(f"{GDIR}/PIXEL_PROVENANCE.md", "w") as f:
        f.write("""# PIXEL PROVENANCE (canonical) — S82-GFX-REVOLUTION

## Instrument

`MINIANDROID_GFX_PROVENANCE=<path.json>` env on any run writes a small
JSON (Git-friendly):

```
{ "instrument": "MINIANDROID_GFX_PROVENANCE",
  "events": [ { origin, resid, path, ASSET_FOUND, RESOURCE_RESOLVED,
                DECODED, BITMAP_CREATED, VIEW_RECEIVED, DRAW_CALLED,
                width, height, color_type, src_density, dst{...},
                FAILURE? } ],
  "frame_census": [ { frame, total_px, nonwhite_px, unique_colors,
                      top_colors_rgb } ],
  "screenshot": { path, SCREENSHOT_CAPTURED, nonwhite_px, unique_colors } }
```

Origins: `imageview-direct` (AXML src path), `imageview-resid` (resid
chain), `background-bitmap`, `bitmapfactory-decode` (BitmapFactory.decode*
family), `canvas-drawBitmap` (CanvasShadow replay: BITMAP_RESOLVED +
REPLAYED bits).

## Divergence-read rules (§6 law, restated as executable predicates)

- `DECODED=1, DRAW_CALLED=0` → do NOT touch the decoder; the fault is in
  view wiring/paint stage.
- `DRAW_CALLED=1, nonwhite_px≈0` → canvas→surface fault (composition).
- `SCREENSHOT_CAPTURED=1 but flat` → capture/composition audit.
- Never blame the previous stage without its bit recorded.

## Fixture ladder (golden probes, §5)

| fixture | level | asserts |
|---|---|---|
| l0_solid | L0 | ColorDrawable bg + TextView + Button |
| l1_quadrant | L1 | RGBA PNG quadrants r/g/b/k + alpha checker |
| l2_colortypes | L2 | PNG color types 0/2/3/4/6 + palette tRNS |
| l3_density | L3 | mdpi..xxxhdpi variant pick + scale |
| l4_xmldrawables | L4 | shape/gradient/layer-list/selector bg |
| l5_canvas | L5 | drawRect fill/stroke, drawPath, drawText, save/clip/restore |
| l6_glsurface | L6 | GLSurfaceView clear color (today: expected FAIL — frontier) |

Build: `python3 scripts/s82gfx_gen_fixtures.py` +
`scripts/build/build_fixture_apk.sh` (ECJ+D8+aapt2, no Android SDK).
Run+assert: `python3 scripts/s82gfx_run_ladder.py` →
`run/s82gfx/LADDER_VERDICT.json`.

Status at HEAD: 6/7 PASS (l6 = documented F-NEW-157 frontier).
""")

    n_game_unlocked = len([1 for t in matrix["TITLES"] if False])  # placeholder
    with open(f"{GDIR}/GRAPHICS_FIX_FANOUT.md", "w") as f:
        f.write(f"""# GRAPHICS FIX FANOUT (canonical) — S82-GFX-REVOLUTION

Question every fix must answer: **how many titles does this unlock?**

## F-NEW-158 fanout (fixed this wave)

- Direct fixture proof: l0_solid + l4_xmldrawables (2 fixtures, 4 drawables
  + ColorDrawable path).
- Real-corpus proof: GAME-004 re-run palette delta unique colors
  111 → 201 (evidence: run/s82gfx/fanout/GAME-004/ + FANOUT_RESULT.json;
  state fields intentionally unchanged pending full re-derivation).
- Corpus reach (static): every title whose UI builds backgrounds
  programmatically — families B/C/D/E cover 37/38/30/38 of the 41 executed
  APKs scanned (graphics_families.json). Exact per-title detector pending:
  run the dex-marker scan (s82gfx_family_scan.py) over the remaining 161
  APKs (disk-guarded lazy materialization).

## F-NEW-159 fanout (open)

Re-traced ×2 in the fanout probe (MAND-002, APP-001); shares the
F-NEW-156 blast radius (35 titles). Unlocks count = titles in the
F-NEW-156 fanout whose trace contains these two exact NPE signatures —
the fanout probe logs are the detector input.

## Fanout discipline (§18/§19 law)

1. fix lands → 2. scan corpus for the signature (static first) →
3. re-run ONLY the affected subset → 4. update every affected title issue
→ 5. record before/after palettes + SHA256s in the matrix.
""")

    # ---- evidence JPGs -----------------------------------------------------
    ev = f"{ROOT}/docs/evidence/s82gfx"
    os.makedirs(ev, exist_ok=True)
    from PIL import Image
    copied = []
    for name in ["l0_solid", "l1_quadrant", "l2_colortypes", "l3_density",
                 "l4_xmldrawables", "l5_canvas", "l6_glsurface"]:
        frames = sorted(
            glob.glob(f"{ROOT}/run/s82gfx/{name}/frames/frame_*.png"))
        if not frames:
            continue
        im = Image.open(frames[-1]).convert("RGB")
        im.thumbnail((540, 960))
        jp = f"{ev}/{name}.jpg"
        im.save(jp, "JPEG", quality=72)
        copied.append(jp)
    with open(f"{ev}/SHA256SUMS", "w") as f:
        for p in sorted(copied) + [f"{ev}/../s82gfx/SHA256SUMS"]:
            pass
    lines = []
    for p in sorted(glob.glob(f"{ev}/*.jpg")) + \
             sorted(glob.glob(f"{ROOT}/run/s82gfx/fanout/*/screenshot.png")):
        lines.append(f"{sha256_file(p)}  {os.path.relpath(p, ROOT)}")
    with open(f"{ev}/SHA256SUMS", "w") as f:
        f.write("\n".join(lines) + "\n")

    print("outputs written:",
          f"{AUD}/GRAPHICS_GAP_MATRIX.json,", f"{GDIR}/*.md")
    print("evidence:", len(lines), "hashed files in", ev)


if __name__ == "__main__":
    main()
