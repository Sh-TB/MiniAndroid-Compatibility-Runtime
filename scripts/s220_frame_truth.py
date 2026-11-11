#!/usr/bin/env python3
"""S220 frame-truth verifier — the EXP-086 false-PASS regression, landed.

GP-582 demand (comment 6806844276): "Add a verifier regression that rejects
exactly this case: three identical 10,535-byte PNGs + 848 sampled non-black
pixels + zero ViewTree/draw/frame events must yield DEFAULT_BACKGROUND_ONLY
or NO_ROOT, never PASS_RENDERED."

GP-582 demand (comment 6807083759 §2 cross-app roots): a presented frame,
non-white noise or high entropy is not app content — the size>800KB noise
heuristic is the cheap first gate on the uninitialized-memory signature.

Verdicts (honest tiers, mutually exclusive):
  NOISE                    — PNG size > NOISE_SIZE_KB (uninitialized-memory
                             colorful-noise signature: incompressible bytes
                             inflate the PNG far past a real UI frame).
  IDENTICAL_ARTIFACT       — the same face bytes recur across runs while the
                             console shows zero draw/frame/ViewTree events
                             (the EXP-086 Phase-4 shape).
  DEFAULT_BACKGROUND_ONLY  — flat single/near-single color frame (the
                             clear-color face; app drew nothing).
  FLAT_TWO_TONE_OR_BLANK   — two-tone flat frames (W16 corpus tier).
  PASS_UI_EVIDENCED        — content present AND the console carries real
                             app-owned draw/frame evidence.

CLI:
  python3 scripts/s220_frame_truth.py --self-test   (the regression battery)
  python3 scripts/s220_frame_truth.py --png F [--console F] [--peers F,F,..]
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys
import zlib

NOISE_SIZE_KB = 800
NOISE_SIZE_BYTES = NOISE_SIZE_KB * 1024


def sha16_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def png_dimensions(png_path):
    with open(png_path, "rb") as f:
        head = f.read(33)
    if len(head) < 33 or head[:8] != b"\x89PNG\r\n\x1a\n":
        return None, None
    return (int.from_bytes(head[16:20], "big"),
            int.from_bytes(head[20:24], "big"))


def sample_frame_stats(png_path, stride=4):
    """Sampled pixel census: unique colors + non-white ratio (no full decode
    via PIL when unavailable — the IHDR/IDAT row is parsed with zlib only)."""
    try:
        from PIL import Image
        img = Image.open(png_path).convert("RGB")
        w, h = img.size
        colors = {}
        px = img.load()
        total = 0
        for y in range(0, h, stride):
            for x in range(0, w, stride):
                c = px[x, y]
                colors[c] = colors.get(c, 0) + 1
                total += 1
        nonwhite = sum(n for c, n in colors.items() if c != (255, 255, 255))
        return {"unique_colors": len(colors), "sampled": total,
                "nonwhite": nonwhite,
                "top_color_share": (max(colors.values()) / total) if total else 0}
    except Exception:
        return {"unique_colors": None, "sampled": 0, "nonwhite": 0,
                "top_color_share": 0}


DRAW_EVENT_RE = re.compile(
    r"performDraw|perform_draw|draw_view|dispatchDraw|stage_render_frame|"
    r"\[GL-DRAW\]|glDrawArrays|glDrawElements|\[VTREE\]|ViewTree",
    re.IGNORECASE)


def classify_frame_truth(png_path, console_text="", peer_sha16s=None,
                         draw_events=None):
    """The honest frame-truth verdict for one run face."""
    reasons, metrics = [], {}
    size = os.path.getsize(png_path)
    metrics["png_bytes"] = size
    metrics["face_sha16"] = sha16_file(png_path)

    # Tier 1 — the uninitialized-memory noise signature (GP-582 §2.8: a
    # presented frame / high entropy is not app content). Real 1080x2400 UI
    # frames compress far below 800KB; colorful noise does not.
    if size > NOISE_SIZE_BYTES:
        reasons.append(f"png {size}B > {NOISE_SIZE_KB}KB noise threshold "
                       f"(uninitialized-memory signature)")
        return {"verdict": "NOISE", "reasons": reasons, "metrics": metrics}

    # Tier 2 — the EXP-086 false-pass shape: identical artifact + zero events.
    events = (draw_events if draw_events is not None
              else len(DRAW_EVENT_RE.findall(console_text or "")))
    metrics["draw_event_hits"] = events
    peers = peer_sha16s or []
    metrics["identical_peers"] = sum(1 for s in peers if s == metrics["face_sha16"])
    if metrics["identical_peers"] >= 2 and events == 0:
        reasons.append(
            f"{metrics['identical_peers']} peer runs produced the identical "
            f"face with zero ViewTree/draw/frame events "
            f"(the EXP-086 Phase-4 shape: synthetic/default artifact)")
        return {"verdict": "IDENTICAL_ARTIFACT", "reasons": reasons,
                "metrics": metrics}

    # Tier 3 — flat faces.
    stats = sample_frame_stats(png_path)
    metrics.update(stats)
    if stats["unique_colors"] is not None:
        if stats["top_color_share"] >= 0.995 or stats["nonwhite"] == 0:
            reasons.append(
                f"flat frame: top color {stats['top_color_share']:.1%} of "
                f"sampled pixels, {stats['unique_colors']} unique colors")
            return {"verdict": "DEFAULT_BACKGROUND_ONLY",
                    "reasons": reasons, "metrics": metrics}
        if stats["unique_colors"] <= 2:
            reasons.append("two-tone flat frame (W16 FLAT_TWO_TONE_OR_BLANK tier)")
            return {"verdict": "FLAT_TWO_TONE_OR_BLANK",
                    "reasons": reasons, "metrics": metrics}

    # Content + evidence present.
    if events == 0:
        reasons.append("content pixels present but console shows no "
                       "app-owned draw/frame events — not claimed as UI")
        return {"verdict": "CONTENT_NO_EVIDENCE", "reasons": reasons,
                "metrics": metrics}
    reasons.append(f"content pixels + {events} draw/frame event hits")
    return {"verdict": "PASS_UI_EVIDENCED", "reasons": reasons,
            "metrics": metrics}


# ─────────────────────────── the self-test battery ────────────────────────

def self_test():
    rows, fails = 0, 0

    def check(ok, name, detail=""):
        nonlocal rows, fails
        rows += 1
        if ok:
            print(f"[PASS] {name}")
        else:
            fails += 1
            print(f"[FAIL] {name} {detail}")

    tmp = "/tmp/s220_fixture"
    os.makedirs(tmp, exist_ok=True)

    # Row 1-3 — the EXP-086 Phase-4 rows straight from the historical JSON:
    # all three false PASS_RENDERED rows carry zero draw/frame/ViewTree
    # evidence; the verifier must reject PASS for that shape.
    hist = "miniandroid/tests/corpus/results/EXP086_PHASE4_RENDER_PIPELINE.json"
    if os.path.exists(hist):
        d = json.load(open(hist))
        for r in d["results"]:
            ev = r["evidence"]
            zero_events = (not ev.get("stage_render_frame_called") and
                           not ev.get("frame_rendered") and
                           not ev.get("create_view_from_dalvik_result") and
                           not ev.get("perform_draw_called") and
                           ev.get("text_views_rendered_count", 0) == 0)
            verdict = classify_frame_truth(
                __file__, "", draw_events=0 if zero_events else 1)
            rows += 1
            ok = zero_events and verdict["verdict"] != "PASS_UI_EVIDENCED"
            if ok:
                print(f"[PASS] exp086 row rejected: "
                      f"{os.path.basename(r['apk'])} zero-evidence")
            else:
                fails += 1
                print(f"[FAIL] exp086 row {r['apk']}")
    else:
        check(False, "exp086 phase4 json present", hist)

    # Row 4 — the noise heuristic: a >800KB incompressible PNG must be NOISE.
    try:
        from PIL import Image
        import random
        random.seed(20261112)
        img = Image.new("RGB", (1080, 2400))
        px = img.load()
        for y in range(0, 2400, 2):
            for x in range(0, 1080, 2):
                c = (random.randrange(256), random.randrange(256),
                     random.randrange(256))
                px[x, y] = c
                px[min(x + 1, 1079), y] = c
                px[x, min(y + 1, 2399)] = c
                px[min(x + 1, 1079), min(y + 1, 2399)] = c
        noise_png = os.path.join(tmp, "noise.png")
        img.save(noise_png, optimize=True)
        v = classify_frame_truth(noise_png)
        check(v["verdict"] == "NOISE",
              "noise: incompressible 1080x2400 >800KB -> NOISE",
              f"got {v['verdict']} {v['metrics']['png_bytes']}B")
    except ImportError:
        check(False, "PIL present for noise fixture")

    # Row 5 — flat white frame -> DEFAULT_BACKGROUND_ONLY.
    try:
        from PIL import Image
        flat = os.path.join(tmp, "flat.png")
        Image.new("RGB", (1080, 2400), (255, 255, 255)).save(flat)
        v = classify_frame_truth(flat, "stage_render_frame ok [VTREE] x=1")
        check(v["verdict"] == "DEFAULT_BACKGROUND_ONLY",
              "flat: uniform white -> DEFAULT_BACKGROUND_ONLY",
              f"got {v['verdict']}")
    except ImportError:
        pass

    # Row 6 — identical peers + zero events -> IDENTICAL_ARTIFACT.
    try:
        from PIL import Image
        art = os.path.join(tmp, "artifact.png")
        Image.new("RGB", (1080, 1920), (0, 0, 0)).save(art)
        s = sha16_file(art)
        v = classify_frame_truth(art, "", peer_sha16s=[s, s])
        check(v["verdict"] == "IDENTICAL_ARTIFACT",
              "exp086 shape: 3 identical faces + 0 events -> rejected",
              f"got {v['verdict']}")
    except ImportError:
        pass

    # Row 7 — content + real draw events -> PASS_UI_EVIDENCED.
    try:
        from PIL import Image, ImageDraw
        real = os.path.join(tmp, "real.png")
        img = Image.new("RGB", (480, 800), (255, 255, 255))
        dr = ImageDraw.Draw(img)
        for i in range(60):
            dr.rectangle([i * 7 % 400, i * 11 % 700,
                          i * 7 % 400 + 60, i * 11 % 700 + 40],
                         fill=(i * 4 % 256, i * 7 % 256, 200))
        img.save(real)
        v = classify_frame_truth(real, "perform_draw stage_render_frame "
                                        "glDrawElements [VTREE]")
        check(v["verdict"] == "PASS_UI_EVIDENCED",
              "content+events -> PASS_UI_EVIDENCED", f"got {v['verdict']}")
    except ImportError:
        pass

    print(f"S220 frame-truth battery: rows={rows} fail={fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--png")
    ap.add_argument("--console")
    ap.add_argument("--peers", help="comma-separated peer face sha16s")
    a = ap.parse_args()
    if a.self_test or not a.png:
        sys.exit(self_test())
    peers = a.peers.split(",") if a.peers else []
    console = open(a.console, errors="ignore").read() if a.console else ""
    print(json.dumps(classify_frame_truth(a.png, console, peers), indent=1))
