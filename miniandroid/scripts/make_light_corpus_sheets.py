#!/usr/bin/env python3
"""Build the curated light-corpus proof sheets into docs/light_corpus/.

Inputs: runtime-produced click-evidence frames (run/light_corpus/evidence).
Output: one click-sequence strip per required app + a launch grid of the
whole corpus. Pixels are copied 1:1 from runtime PNGs — the only additions
are textual captions drawn beside (never over) the frames.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parent.parent
EV = REPO / "run/light_corpus/evidence"
DOCS = REPO / "docs/light_corpus"

REQUIRED = ["simplestopwatch", "gmdice", "unote", "chessclock"]
OTHERS = ["bgclockhansdezwart", "headingcalculator", "tinymusicplayer",
          "microtimer", "stopwatchmuellerma", "simplekeyboard",
          "notesbillthefarmer", "tictactoeemmanuelmess"]

TH_W, TH_H = 180, 320


def thumb(img: Image.Image) -> Image.Image:
    return img.convert("RGB").resize((TH_W, TH_H), Image.LANCZOS)


def strip_for(app: str) -> Path | None:
    frames = sorted((EV / app / "runA" / "frames").glob("frame_*.png"))
    if not frames:
        return None
    cols = len(frames)
    cap_h = 34
    sheet = Image.new("RGB", (cols * (TH_W + 6) + 6, TH_H + cap_h + 10), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(frames):
        im = thumb(Image.open(f))
        x = 6 + i * (TH_W + 6)
        sheet.paste(im, (x, 6))
        d.text((x + 4, TH_H + 10), f"frame {i}", fill=(220, 220, 220))
    out = DOCS / f"{app}_click_sequence.png"
    sheet.save(out)
    return out


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    made = []
    for app in REQUIRED:
        p = strip_for(app)
        if p:
            made.append(p.name)

    # launch grid: every corpus app's launch frame (frame_000 or screenshot)
    names = REQUIRED + OTHERS
    tiles = []
    for app in names:
        f = EV / app / "runA" / "frames" / "frame_000.png"
        if not f.exists():
            f = EV / app / "runA" / "screenshot.png"
        if not f.exists():
            f = REPO / "run/light_corpus/fix5" / app / "screenshot.png"
        if f.exists():
            tiles.append((app, thumb(Image.open(f))))
        else:
            tiles.append((app, Image.new("RGB", (TH_W, TH_H), (60, 0, 0))))
    cols = 6
    rows = (len(tiles) + cols - 1) // cols
    cap_h = 26
    grid = Image.new("RGB", (cols * (TH_W + 6) + 6, rows * (TH_H + cap_h + 6) + 6),
                     (24, 24, 24))
    d = ImageDraw.Draw(grid)
    for i, (app, im) in enumerate(tiles):
        x = 6 + (i % cols) * (TH_W + 6)
        y = 6 + (i // cols) * (TH_H + cap_h + 6)
        grid.paste(im, (x, y))
        d.text((x + 2, y + TH_H + 4), app[:30], fill=(220, 220, 220))
    grid.save(DOCS / "corpus_launch_grid.png")
    print("sheets:", [m for m in made], "+ corpus_launch_grid.png")


if __name__ == "__main__":
    sys.exit(main())
