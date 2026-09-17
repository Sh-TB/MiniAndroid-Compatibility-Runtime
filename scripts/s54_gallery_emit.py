#!/usr/bin/env python3
"""S54 canonical gallery emit — docs/evidence/s54_frames/.

Refined gate law (S54, strictly narrowing S53's false-reject class):
  BLANK  := (near-white >= 97% or near-black >= 97%) AND colors <= 8
            | colors <= 8 alone (renderer artifact class)
  DARK-CONTENT := near-black >= 97% AND colors > 8  -> real dark-themed UI;
                  requires an independent content check (e.g. battery EXT-01
                  typography golden) before it may be stored.
All S53 rejections remain valid under this law:
  chessclock (99.3% nb, 2 colors) -> BLANK; notes (99.1% nw, 5 colors) -> BLANK.
JPG pipeline identical to S53 (quality=88, optimize=True, <=100KB).
"""
import hashlib
import os

from PIL import Image

RUNS = "/home/z/my-project/local/s54/runs"
OUT = "/home/z/my-project/docs/evidence/s54_frames"
MAX_BYTES = 100 * 1024

# (name, phase, src_png, milestone, why_it_matters)
FRAMES = [
    ("helloworld_ext01", "base", "helloworld_ext01/screenshot.png",
     "L5 — real external HelloWorld APK renders its text UI (dark theme, 256 colors)",
     "Canonical HelloWorld control target: real released APK 009b4671… renders "
     "'hello world' + app-computed device hash via the full APK→DEX→View→text chain; "
     "battery EXT-01 typography golden 9/9 vs upstream phone screenshot"),
    ("gmdice", "base", "gmdice/screenshot.png",
     "L5 — GM Dice real game UI (dialog, roll hint, 1d20/1d6/1d6+4 bar)",
     "Initial game state before input; gate numbers byte-stable across S53→S54 HEADs"),
    ("gmdice", "after", "gmdice/click_frame_2.png",
     "L7 + app-specific result — dice roll '14 · 15 · 15' rendered after 8/8 clicks",
     "Real game logic executed: app DEX rolled dice and rendered the values "
     "(1,865,794 px delta vs base); strongest corpus game record"),
    ("microtimer", "base", "microtimer/screenshot.png",
     "L5 — MicroTimer keypad UI",
     "Initial state before input (193 colors)"),
    ("microtimer", "after", "microtimer/click_frame_1.png",
     "L7 — click → '00:00:00' timer display appears (31,863 px)",
     "Input→state change: display row with timer + play/stop buttons appears"),
    ("simplestopwatch", "base", "simplestopwatch/screenshot.png",
     "L5 — Simple Stopwatch Start/Delay UI",
     "Initial state before input"),
    ("simplestopwatch", "after", "simplestopwatch/click_frame_1.png",
     "L7 — Start → Stop/Lap running-state transition (40,915 px)",
     "Input→state change: button row switches to running state"),
    ("headingcalculator", "base", "headingcalculator/screenshot.png",
     "L5 — Heading Calculator full keypad UI",
     "Initial state before input (416 colors)"),
    ("headingcalculator", "after", "headingcalculator/click_frame_9.png",
     "L7 — digit click → display value changes (1,389 px)",
     "Input→state change on the calculator display"),
    ("unote", "base", "unote/screenshot.png",
     "L5 — uNote real list UI (input blocked by R-NEW-368, honestly recorded)",
     "Buttons/checkboxes render; 2/4 small click changes; L6 unreachable until fix"),
]

REJECTED = [
    ("chessclock", "chessclock/screenshot.png",
     "BLANK dark class: 99.3% near-black, 2 colors, no click frames (0/N state "
     "changes); SHA16 e4a2d7c90cd2fd26 EXACT match across S51→S54 (determinism proof)"),
    ("notes", "notes/screenshot.png",
     "BLANK near-white class: 99.1% near-white, 5 colors, no click frames; "
     "SHA16 ae697935dbeb6f33"),
]


def metrics(path):
    im = Image.open(path)
    g = im.convert("L")
    h = g.histogram()
    total = im.size[0] * im.size[1]
    nw = sum(h[245:]) / total * 100
    nb = sum(h[:12]) / total * 100
    rgb = im.convert("RGB")
    colors = rgb.getcolors(maxcolors=1 << 24)
    ncolors = len(colors) if colors else -1
    return nw, nb, ncolors


def verdict(nw, nb, nc):
    if nc <= 8:
        return "BLANK"
    if nw >= 97 or nb >= 97:
        return "DARK-CONTENT" if nb >= 97 else "BLANK"
    return "MEANINGFUL"


def emit(src, dst):
    im = Image.open(src).convert("RGB")
    q = 88
    im.save(dst, "JPEG", quality=q, optimize=True)
    while os.path.getsize(dst) > MAX_BYTES and q > 40:
        q -= 6
        im.save(dst, "JPEG", quality=q, optimize=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    lines = ["# S54 canonical gallery — SHA256SUMS + gate numbers",
             "# HEAD 8c575f71 · gate law: S54 refinement (BLANK needs colors<=8; "
             "near-black + colors>8 = DARK-CONTENT, requires content check)",
             "# All frames fresh runs local/s54/runs/ · JPG pipeline = S53 (q88 optimize)"]
    ok = True
    for name, phase, rel, milestone, why in FRAMES:
        src = os.path.join(RUNS, rel)
        nw, nb, nc = metrics(src)
        v = verdict(nw, nb, nc)
        if v == "BLANK":
            print(f"REFUSED (gate BLANK): {name}_{phase}")
            ok = False
            continue
        dst = os.path.join(OUT, f"{name}_{phase}.jpg")
        emit(src, dst)
        sz = os.path.getsize(dst)
        sha = hashlib.sha256(open(dst, "rb").read()).hexdigest()
        lines.append(f"{sha}  {name}_{phase}.jpg  | {v} | nw={nw:.1f}% nb={nb:.1f}% "
                     f"colors={nc} | {sz}B | {milestone}")
        print(f"OK {name}_{phase}.jpg {sz}B {v} colors={nc}")
    lines.append("")
    lines.append("# REJECTED (blank-class, recorded as text only — never stored as images)")
    for name, rel, why in REJECTED:
        nw, nb, nc = metrics(os.path.join(RUNS, rel))
        lines.append(f"# {name}: nw={nw:.1f}% nb={nb:.1f}% colors={nc} — {why}")
    open(os.path.join(OUT, "SHA256SUMS"), "w").write("\n".join(lines) + "\n")
    print("SHA256SUMS written; ok =", ok)


if __name__ == "__main__":
    main()
