#!/usr/bin/env python3
"""s80_evidence_package.py — S80 evidence bundle assembly.

Packages the wave's artifacts into docs/evidence/s80/ per the evidence
law: key gameplay frames as JPG 540x960 q72 <=100KB; the three gameplay
GIFs verbatim (website mirrors); the ladder sweep report; SHA256SUMS.
"""
import glob
import hashlib
import json
import os
import shutil

from PIL import Image

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/docs/evidence/s80"
os.makedirs(OUT, exist_ok=True)


def to_jpg(src_png, dst_jpg, size=(540, 960), q=72):
    im = Image.open(src_png).convert("RGB")
    if im.size != size:
        im = im.resize(size, Image.LANCZOS)
    im.save(dst_jpg, "JPEG", quality=q, optimize=True)
    kb = os.path.getsize(dst_jpg) / 1024
    assert kb <= 100, f"{dst_jpg} is {kb:.0f}KB (>100KB)"
    return kb


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    written = []

    # 1. gameplay GIFs (verbatim website mirrors)
    for name in ("snake_gameplay.gif", "tetris_gameplay.gif",
                 "g2048_gameplay.gif"):
        src = f"{ROOT}/download/s80/{name}"
        dst = f"{OUT}/{name}"
        shutil.copyfile(src, dst)
        written.append(dst)

    # 2. key gameplay frames -> JPG (evidence law)
    key_frames = {
        "snake": "run/s80_sd_autoplay/final_run",
        "tetris": "run/s80_tet_autoplay/final_run",
        "g2048": "run/s80_2048_autoplay/final_run",
    }
    for tag, run in key_frames.items():
        frames = sorted(glob.glob(f"{ROOT}/{run}/frames/frame_*.png"))
        if not frames:
            print(f"WARN: no frames for {tag}")
            continue
        picks = {frames[len(frames) // 3]: "a", frames[2 * len(frames) // 3]: "b",
                 frames[-1]: "c"}
        for src, suffix in picks.items():
            dst = f"{OUT}/{tag}_frame_{suffix}.jpg"
            kb = to_jpg(src, dst)
            written.append(dst)
            print(f"{tag}_{suffix}.jpg {kb:.0f}KB")

    # 3. ladder sweep report
    sweep = f"{ROOT}/run/s80_ladder/sweep_report.json"
    if os.path.exists(sweep):
        dst = f"{OUT}/sweep_report.json"
        shutil.copyfile(sweep, dst)
        written.append(dst)

    # 4. driver logs (gameplay provenance)
    for src, dst in [
        (f"{ROOT}/run/s80_sd_autoplay_driver.out", "snake_autoplay_log.txt"),
        (f"{ROOT}/run/s80_tet_autoplay/../s80_tet_autoplay/../s80_tet_autoplay_driver.out",
         "tetris_autoplay_log.txt"),
        (f"{ROOT}/run/s80_2048_driver.out", "g2048_autoplay_log.txt"),
    ]:
        if os.path.exists(src):
            shutil.copyfile(src, f"{OUT}/{dst}")
            written.append(f"{OUT}/{dst}")

    # 5. SHA256SUMS
    with open(f"{OUT}/SHA256SUMS", "w") as f:
        for p in sorted(written):
            rel = os.path.relpath(p, OUT)
            f.write(f"{sha256(p)}  {rel}\n")
    print(f"packaged {len(written)} artifacts + SHA256SUMS")


if __name__ == "__main__":
    main()
