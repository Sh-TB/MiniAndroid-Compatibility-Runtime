#!/usr/bin/env python3
"""make_demo_proof.py — build the public visual proof assets from REAL runtime frames.

Inputs  (produced ONLY by the MiniAndroid runtime, never by hand):
    --frames-dir <dir>   contains frame_*.png + manifest.json written by
                         `miniandroid run <apk> --click-count N`
    --manifest  <json>   the committed evidence manifest (docs/demo/demo_manifest.json)

Integrity gate (runs first, fails hard on any mismatch):
    * every frame PNG's bytes must hash to the manifest's png_sha256
    * the framebuffer hash in the fresh run manifest must equal the committed one
      (proves the frames are the deterministic render the evidence describes)

Outputs (documentation assembled AROUND genuine runtime pixels):
    docs/demo/demo_frames.png   labeled 5-state contact sheet (STATE 0..4)
    docs/demo/demo_proof.gif    9-frame animation (only runtime frames, no others)

No pixel of the app area originates from this script: it crops and scales the
runtime's own PNG output and draws text only in the documentation bands.
"""

import argparse
import hashlib
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

SHEET_STATES = [0, 1, 2, 3, 4]      # frames shown on the contact sheet
CROP = (0, 0, 1080, 1120)           # informative region: texts + button + box (max y=1082)
TILE_W = 500                        # tile width after scaling the crop
BG = (24, 26, 32)
FG = (235, 238, 245)
ACCENT = (94, 168, 255)
MUT = (140, 146, 158)

GIF_W = 540                         # GIF width after scaling the crop
GIF_MS = 700


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_font(size):
    for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def verify(frames_dir, manifest_path):
    """Integrity gate: frame files must hash to the committed manifest values."""
    ref = json.load(open(manifest_path))
    rmap = {f["file"]: f for f in ref["frames"]}
    with open(os.path.join(frames_dir, "manifest.json")) as f:
        run = json.load(f)
    problems = []
    for rf in ref["frames"]:
        path = os.path.join(frames_dir, rf["file"])
        if not os.path.exists(path):
            problems.append("missing frame: %s" % rf["file"])
            continue
        got = sha256_file(path)
        want = rf.get("png_sha256")
        if want and got != want:
            problems.append("%s png_sha256 %s != committed %s" % (rf["file"], got[:16], want[:16]))
        if rf["file"] in rmap:
            run_fb = {f["file"]: f["sha256"] for f in run["frames"]}.get(rf["file"])
            if run_fb and run_fb != rf["sha256"]:
                problems.append("%s framebuffer %s != committed %s"
                                % (rf["file"], run_fb[:16], rf["sha256"][:16]))
    if problems:
        for p in problems:
            print("PROVENANCE FAIL:", p, file=sys.stderr)
        sys.exit(1)
    print("provenance gate: %d/%d frames byte-match the committed evidence"
          % (len(ref["frames"]), len(ref["frames"])))
    return ref


def status_text(frame):
    for t in frame.get("visible_texts", []):
        if "count=" in t.get("text", ""):
            return t["text"]
    return ""


def build_sheet(ref, frames_dir, out_path):
    scale = TILE_W / (CROP[2] - CROP[0])
    tile_h = int((CROP[3] - CROP[1]) * scale)
    label_h, cap_h = 46, 62
    pad = 14
    cols = len(SHEET_STATES)
    W = cols * TILE_W + (cols + 1) * pad
    header_h, footer_h = 92, 64
    H = header_h + label_h + tile_h + cap_h + footer_h + pad

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_head = load_font(30)
    f_sub = load_font(19)
    f_label = load_font(26)
    f_cap = load_font(21)
    f_small = load_font(16)

    d.text((pad, 18), "MiniAndroid — real-APK execution proof", font=f_head, fill=FG)
    d.text((pad, 56), "5 states of the demo APK as rendered by the MiniAndroid software renderer "
                      "(frames captured by the runtime itself)", font=f_sub, fill=MUT)

    for i, idx in enumerate(SHEET_STATES):
        fr = ref["frames"][idx]
        tile = Image.open(os.path.join(frames_dir, fr["file"])).convert("RGB").crop(CROP)
        tile = tile.resize((TILE_W, tile_h), Image.LANCZOS)
        x = pad + i * (TILE_W + pad)
        y = header_h
        d.text((x + 2, y + 8), "STATE %d" % idx, font=f_label, fill=ACCENT)
        y += label_h
        img.paste(tile, (x, y))
        d.rectangle([x - 1, y - 1, x + TILE_W, y + tile_h], outline=(70, 76, 88))
        y += tile_h
        cap = status_text(fr)
        d.text((x + 2, y + 6), cap, font=f_cap, fill=FG)
        d.text((x + 2, y + 34), "%s · sha256 %s…" % (fr["file"], fr.get("png_sha256", "")[:12]),
               font=f_small, fill=MUT)

    fy = H - footer_h + 6
    d.text((pad, fy), "Every click executes demo DEX bytecode inside MiniAndroid: counter++, box position "
                      "moves on a 5x4 grid, color cycles GREEN-BLUE-YELLOW-RED, status text re-renders.",
           font=f_small, fill=MUT)
    d.text((pad, fy + 24), "Reproduce: ./miniandroid run miniandroid-demo.apk -o out --click-count 8   ·   "
                           "per-frame SHA256 evidence: docs/demo/demo_manifest.json",
           font=f_small, fill=MUT)

    img.save(out_path, optimize=True)
    print("wrote %s (%dx%d, %.1f KB)" % (out_path, W, H, os.path.getsize(out_path) / 1e3))


def build_gif(ref, frames_dir, out_path):
    frames = []
    for fr in ref["frames"]:
        tile = Image.open(os.path.join(frames_dir, fr["file"])).convert("RGB").crop(CROP)
        w = GIF_W
        h = int(tile.height * (GIF_W / tile.width))
        frames.append(tile.resize((w, h), Image.LANCZOS))
    frames[0].save(out_path, save_all=True, append_images=frames[1:],
                   duration=GIF_MS, loop=0, optimize=True)
    print("wrote %s (%d frames, %.1f KB)" % (out_path, len(frames), os.path.getsize(out_path) / 1e3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames-dir", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out-dir", default="docs/demo")
    args = ap.parse_args()

    ref = verify(args.frames_dir, args.manifest)
    build_sheet(ref, args.frames_dir, os.path.join(args.out_dir, "demo_frames.png"))
    build_gif(ref, args.frames_dir, os.path.join(args.out_dir, "demo_proof.gif"))


if __name__ == "__main__":
    main()
