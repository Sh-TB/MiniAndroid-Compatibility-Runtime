#!/usr/bin/env python3
"""CONT-11 TRAIN-1 analysis: does the dooz board actually render after the tap?

Evidence standard (honest):
  PASS  = last frame board-region PNG has >2 distinct colors AND at least one
          pixel matches the dooz primary (#494E9B-ish) cell fill.
  FAIL  = blank/white face -> report throw families instead.
canvas_ops.jsonl is the engine TEXT per-op format: field[1]=op name, field[3]=y.
"""
import glob, hashlib, os, sys
from collections import Counter

OUT = "/home/z/my-project/tmp/s134_train3_out"

def census():
    p = os.path.join(OUT, "canvas_ops.jsonl")
    if not os.path.exists(p):
        print("canvas_ops: MISSING"); return
    ops, lines = Counter(), 0
    with open(p, errors="replace") as f:
        for ln in f:
            lines += 1
            parts = ln.split("|")
            if len(parts) > 1:
                ops[parts[1].strip()] += 1
    print(f"canvas_ops lines={lines}")
    for k, v in ops.most_common(12):
        print(f"  {k}: {v}")

def png_probe():
    frames = sorted(glob.glob(os.path.join(OUT, "frames", "*.png")))
    print(f"frames={len(frames)}")
    if not frames:
        return
    try:
        from PIL import Image
    except ImportError:
        print("PIL missing"); return
    picks = [0, 10, 29, 31, 60, 90, len(frames) - 1]
    for i in picks:
        if i >= len(frames):
            continue
        im = Image.open(frames[i]).convert("RGB")
        w, h = im.size
        # board region: game screen bottom half, center 60% width
        box = im.crop((int(w*0.2), int(h*0.45), int(w*0.8), int(h*0.85)))
        cols = box.getcolors(maxcolors=100000)
        n = len(cols) if cols else -1
        top = sorted(cols or [], reverse=True)[:4]
        print(f"frame_{i:03d} size={w}x{h} board_distinct={n} top={[(c,rgb) for c,rgb in top]}")

def pins():
    for name in ["canvas_ops.jsonl", "throw_sites.log", "report.md"]:
        p = os.path.join(OUT, name)
        if os.path.exists(p):
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
            print(f"pin {name}={h} bytes={os.path.getsize(p)}")
    for f in sorted(glob.glob(os.path.join(OUT, "frames", "*.png")))[-3:]:
        h = hashlib.sha256(open(f, "rb").read()).hexdigest()[:16]
        print(f"pin {os.path.basename(f)}={h}")

if __name__ == "__main__":
    census(); png_probe(); pins()
