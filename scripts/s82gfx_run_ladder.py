#!/usr/bin/env python3
"""S82-GFX-REVOLUTION P4 — run the golden fixture ladder at HEAD binary,
collect pixel provenance, assert level expectations, emit first-divergence
verdicts. 100% evidence-based: every verdict cites pixels or chain bits.
"""
import glob
import json
import os
import subprocess
import sys
from collections import Counter

ENG = "/home/z/my-project/miniandroid/build/miniandroid"
FIX = "/tmp/my-project/gfx_fixtures"
OUT = "/home/z/my-project/run/s82gfx"

COLORS = lambda px: (px[0], px[1], px[2])


def run_fixture(name, timeout=300):
    apk = f"{FIX}/{name}.apk"
    outdir = f"{OUT}/{name}"
    os.makedirs(outdir, exist_ok=True)
    log = f"{outdir}.log"
    env = dict(os.environ)
    env["MINIANDROID_GFX_PROVENANCE"] = f"{outdir}/provenance.json"
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", "6", "--frame-delay", "300", "-o", outdir, apk]
    with open(log, "w") as lf:
        try:
            rc = subprocess.call(cmd, stdout=lf, stderr=lf,
                                 timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            rc = -1
    return rc, log


def png_pixels(path):
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    return im, im.load(), im.size


def color_counts(png, sample=2):
    im, px, size = png_pixels(png)
    c = Counter()
    for y in range(0, size[1], sample):
        for x in range(0, size[0], sample):
            p = px[x, y]
            c[(p[0], p[1], p[2])] += 1
    return c, size


def has_color(counts, rgb, tol=6, min_hits=3):
    n = 0
    for c, k in counts.items():
        if all(abs(c[i] - rgb[i]) <= tol for i in range(3)):
            n += k
            if n >= min_hits:
                return True
    return False


def verdict(name, ok, checks, provenance_path):
    v = {
        "fixture": name, "PASS": ok, "checks": checks,
        "provenance": provenance_path,
    }
    return v


def chain_summary(prov_path):
    if not os.path.exists(prov_path):
        return {"PROVENANCE_MISSING": True}
    p = json.load(open(prov_path))
    events = p.get("events", [])
    summary = {"events": len(events),
               "shot": p.get("screenshot", {}),
               "origins": Counter(e.get("origin") for e in events)}
    fails = [e for e in events if not e.get("DRAW_CALLED")]
    summary["not_drawn"] = [
        {"origin": e.get("origin"), "path": e.get("path"),
         "ASSET_FOUND": e.get("ASSET_FOUND"),
         "DECODED": e.get("DECODED"),
         "FAILURE": e.get("FAILURE")} for e in fails[:20]
    ]
    drawn = [e for e in events if e.get("DRAW_CALLED")]
    summary["drawn"] = len(drawn)
    if events:
        summary["first_divergence_event"] = fails[0] if fails else None
    return summary


def main():
    os.makedirs(OUT, exist_ok=True)
    results = {}

    # ---------------- L0 baseline
    rc, log = run_fixture("l0_solid")
    frames = sorted(glob.glob(f"{OUT}/l0_solid/frames/frame_*.png"))
    if frames:
        counts, size = color_counts(frames[-1])
        bg = has_color(counts, (20, 40, 60))
        results["l0_solid"] = verdict(
            "l0_solid", bg,
            {"dark_bg_present": bg, "frame": frames[-1], "rc": rc,
             "size": list(size)}, f"{OUT}/l0_solid/provenance.json")
    else:
        results["l0_solid"] = {"fixture": "l0_solid", "PASS": False,
                               "reason": "no frames", "rc": rc}

    # ---------------- L1 quadrant
    rc, log = run_fixture("l1_quadrant")
    frames = sorted(glob.glob(f"{OUT}/l1_quadrant/frames/frame_*.png"))
    if frames:
        counts, size = color_counts(frames[-1])
        checks = {
            "red": has_color(counts, (255, 0, 0)),
            "green": has_color(counts, (0, 255, 0)),
            "blue": has_color(counts, (0, 0, 255)),
            "black": has_color(counts, (0, 0, 0), tol=10),
        }
        checks["PASS"] = all(checks.values())
        results["l1_quadrant"] = verdict(
            "l1_quadrant", checks["PASS"], {"colors": checks, "rc": rc},
            f"{OUT}/l1_quadrant/provenance.json")
    else:
        results["l1_quadrant"] = {"fixture": "l1_quadrant", "PASS": False,
                                  "reason": "no frames", "rc": rc}

    # ---------------- L2 color types
    rc, log = run_fixture("l2_colortypes")
    frames = sorted(glob.glob(f"{OUT}/l2_colortypes/frames/frame_*.png"))
    if frames:
        counts, size = color_counts(frames[-1])
        # palette row: color[5] = (80, 175, 35)-ish pal colors; assert a
        # handful of exact palette colors + grayscale ramp + rgb ramp
        checks = {}
        for i in (1, 5, 9, 15):
            c = (i * 16, 255 - i * 16, (i * 7) % 256)
            checks[f"palette_ct3_{i}"] = has_color(counts, c, tol=8)
        checks["gray_ct0"] = has_color(counts, (128, 128, 128), tol=8)
        checks["rgb_ct2"] = has_color(counts, (255, 128, 0), tol=14)
        checks["ga_ct4"] = has_color(counts, (128, 128, 128), tol=8)
        ok = checks["palette_ct3_5"] and checks["gray_ct0"] and checks["rgb_ct2"]
        checks["PASS"] = bool(ok)
        results["l2_colortypes"] = verdict(
            "l2_colortypes", checks["PASS"], {"colors": checks, "rc": rc},
            f"{OUT}/l2_colortypes/provenance.json")
    else:
        results["l2_colortypes"] = {"fixture": "l2_colortypes",
                                    "PASS": False, "reason": "no frames",
                                    "rc": rc}

    # ---------------- L3 density selection
    rc, log = run_fixture("l3_density")
    frames = sorted(glob.glob(f"{OUT}/l3_density/frames/frame_*.png"))
    if frames:
        counts, size = color_counts(frames[-1])
        variants = {
            "mdpi_red": (255, 0, 0), "hdpi_green": (0, 160, 0),
            "xhdpi_blue": (0, 0, 255), "xxhdpi_yellow": (255, 220, 0),
            "xxxhdpi_magenta": (200, 0, 200),
        }
        picked = [k for k, v in variants.items() if has_color(counts, v, tol=10, min_hits=6)]
        checks = {"selected_variant": picked, "PASS": len(picked) == 1}
        results["l3_density"] = verdict(
            "l3_density", checks["PASS"], checks,
            f"{OUT}/l3_density/provenance.json")
    else:
        results["l3_density"] = {"fixture": "l3_density", "PASS": False,
                                 "reason": "no frames", "rc": rc}

    # ---------------- L4 XML drawables
    rc, log = run_fixture("l4_xmldrawables")
    frames = sorted(glob.glob(f"{OUT}/l4_xmldrawables/frames/frame_*.png"))
    if frames:
        counts, size = color_counts(frames[-1])
        checks = {
            "shape_solid_FF6633": has_color(counts, (0xFF, 0x66, 0x33), tol=12),
            "gradient_mid_purple": has_color(counts, (128, 0, 128), tol=30),
            "layer_white": has_color(counts, (255, 255, 255), tol=4),
            "selector_idle_333333": has_color(counts, (0x33, 0x33, 0x33), tol=12),
        }
        checks["PASS"] = all(checks.values())
        results["l4_xmldrawables"] = verdict(
            "l4_xmldrawables", checks["PASS"], {"colors": checks, "rc": rc},
            f"{OUT}/l4_xmldrawables/provenance.json")
    else:
        results["l4_xmldrawables"] = {"fixture": "l4_xmldrawables",
                                      "PASS": False, "reason": "no frames",
                                      "rc": rc}

    # ---------------- L5 canvas
    rc, log = run_fixture("l5_canvas")
    frames = sorted(glob.glob(f"{OUT}/l5_canvas/frames/frame_*.png"))
    if frames:
        counts, size = color_counts(frames[-1])
        checks = {
            "canvas_bg_F5F0DC": has_color(counts, (245, 240, 220), tol=8),
            "fill_rect_C81E1E": has_color(counts, (200, 30, 30), tol=8),
            "path_green_00A03C": has_color(counts, (0, 160, 60), tol=8),
            "stroke_blue_005AC8": has_color(counts, (0, 90, 200), tol=10),
        }
        checks["PASS"] = all(checks.values())
        results["l5_canvas"] = verdict(
            "l5_canvas", checks["PASS"], {"colors": checks, "rc": rc},
            f"{OUT}/l5_canvas/provenance.json")
    else:
        results["l5_canvas"] = {"fixture": "l5_canvas", "PASS": False,
                                "reason": "no frames", "rc": rc}

    # ---------------- L6 GL surface (F-NEW-157 family)
    rc, log = run_fixture("l6_glsurface")
    frames = sorted(glob.glob(f"{OUT}/l6_glsurface/frames/frame_*.png"))
    log_text = open(log, errors="ignore").read() if os.path.exists(log) else ""
    expected_clear = (26, 153, 230)  # 0.1/0.6/0.9 * 255
    if frames:
        counts, size = color_counts(frames[-1])
        gl_ok = has_color(counts, expected_clear, tol=12, min_hits=20)
        results["l6_glsurface"] = verdict(
            "l6_glsurface", gl_ok,
            {"gl_clear_color_present": gl_ok, "rc": rc,
             "log_excerpt": log_text[-1500:]},
            f"{OUT}/l6_glsurface/provenance.json")
    else:
        results["l6_glsurface"] = {
            "fixture": "l6_glsurface", "PASS": False, "reason": "no frames",
            "rc": rc, "log_excerpt": log_text[-1500:]}

    # chain summaries
    for name, v in results.items():
        v["chain"] = chain_summary(v.get("provenance", f"{OUT}/{name}/provenance.json"))

    json.dump(results, open(f"{OUT}/LADDER_VERDICT.json", "w"), indent=1)
    for name, v in results.items():
        print(f"{name:18s} {'PASS' if v.get('PASS') else 'FAIL'}")
        ch = v.get("chain", {})
        if ch.get("not_drawn"):
            print(f"   not_drawn[0]: {ch['not_drawn'][0]}")
        if ch.get("shot", {}).get("nonwhite_px") is not None:
            print(f"   shot nonwhite={ch['shot']['nonwhite_px']} unique={ch['shot']['unique_colors']}")


if __name__ == "__main__":
    main()
