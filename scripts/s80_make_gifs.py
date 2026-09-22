#!/usr/bin/env python3
"""s80_make_gifs.py — build clean gameplay GIFs from real rendered frames.

Input: frame dirs from the S80 autoplay evidence runs (REAL APK execution
through the MiniAndroid runtime). Output: download/s80/*.gif — downscaled,
uniform-duration, with a thin caption strip (no giant banners).
"""
import glob
import os

from PIL import Image, ImageDraw

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/download/s80"
os.makedirs(OUT, exist_ok=True)

WIDTH = 400          # downscale target width
MAX_SEGMENTS = 96    # per-GIF cap


def build_gif(frame_dir, out_path, caption, pick_every=None, fps=4):
    files = sorted(glob.glob(f"{frame_dir}/frames/frame_*.png"))
    assert files, f"no frames in {frame_dir}"
    n = len(files)
    # choose segments: spread across the run
    seg = pick_every or max(1, n // MAX_SEGMENTS + (1 if n % MAX_SEGMENTS else 0))
    picked = files[::seg]
    # always include the last frame (final state)
    if files[-1] != picked[-1]:
        picked.append(files[-1])

    im0 = Image.open(picked[0]).convert("RGB")
    scale = WIDTH / im0.width
    size = (WIDTH, int(im0.height * scale))

    cap_h = 26
    frames = []
    for f in picked:
        im = Image.open(f).convert("RGB").resize(size, Image.LANCZOS)
        canvas = Image.new("RGB", (size[0], size[1] + cap_h), (12, 16, 28))
        canvas.paste(im, (0, 0))
        d = ImageDraw.Draw(canvas)
        d.text((8, size[1] + 6), caption, fill=(148, 163, 184))
        frames.append(canvas)

    dur = int(1000 / fps)
    frames[0].save(out_path, save_all=True, append_images=frames[1:],
                   duration=dur, loop=0, optimize=True)
    sz = os.path.getsize(out_path)
    print(f"{out_path}: {len(frames)} segments, {sz/1024:.0f} KB "
          f"(from {n} frames, every {seg})")


def build_sprite(frame_dir, out_path, caption=""):
    """Static screenshot (last frame) for the website gallery."""
    files = sorted(glob.glob(f"{frame_dir}/frames/frame_*.png"))
    im = Image.open(files[-1]).convert("RGB")
    scale = WIDTH / im.width
    im = im.resize((WIDTH, int(im.height * scale)), Image.LANCZOS)
    im.save(out_path, optimize=True)
    print(f"{out_path}: {os.path.getsize(out_path)/1024:.0f} KB")


if __name__ == "__main__":
    import sys
    jobs = sys.argv[1] if len(sys.argv) > 1 else "all"

    if jobs in ("all", "tetris"):
        build_gif(f"{ROOT}/run/s80_tet_autoplay/final_run",
                  f"{OUT}/tetris_gameplay.gif",
                  "Mini Tetris - real APK on MiniAndroid runtime",
                  fps=6)
        build_sprite(f"{ROOT}/run/s80_tet_autoplay/final_run",
                     f"{OUT}/tetris_screenshot.jpg")

    if jobs in ("all", "g2048"):
        fd = f"{ROOT}/run/s80_2048_autoplay/final_run"
        if glob.glob(f"{fd}/frames/frame_*.png"):
            build_gif(fd, f"{OUT}/g2048_gameplay.gif",
                      "2048 - real APK on MiniAndroid runtime", fps=4)
            build_sprite(fd, f"{OUT}/g2048_screenshot.jpg")
        else:
            print("2048 final run not ready yet")

    if jobs in ("all", "snake"):
        fd = f"{ROOT}/run/s80_sd_autoplay/final_run"
        if glob.glob(f"{fd}/frames/frame_*.png"):
            build_gif(fd, f"{OUT}/snake_gameplay.gif",
                      "Snake Deluxe - real APK on MiniAndroid runtime", fps=5)
            build_sprite(fd, f"{OUT}/snake_screenshot.jpg")
        else:
            print("snake final run not ready yet")
