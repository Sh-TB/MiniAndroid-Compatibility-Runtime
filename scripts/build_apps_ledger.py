#!/usr/bin/env python3
"""Build APPS_EXECUTION_LEDGER assets: compress evidence screenshots to medium
quality (540px wide, palette-optimized PNG), compute SHA256 of originals and
compressed copies, print a compression report. Originals are NEVER modified
(goldens are hash-pinned by the battery)."""
import hashlib
import json
import os
from PIL import Image

ROOT = "/home/z/my-project"
OUT = os.path.join(ROOT, "miniandroid/docs/evidence/apps_ledger")
os.makedirs(OUT, exist_ok=True)

# (source_path, ledger_name)
IMAGES = [
    ("docs/evidence/hello_color_golden/frame_1080x1920.png",          "hellocolor.png"),
    ("miniandroid/run/s18_hello_run3/screenshot.png",                  "helloworld.png"),
    ("docs/evidence/tictactoe_golden/board_x_wins.png",                "tictactoe_xwins.png"),
    ("miniandroid/run/s27_suite/gmdice.png",                           "gmdice.png"),
    ("miniandroid/run/s26_gmdice_tap/frames/frame_003.png",            "gmdice_after_tap.png"),
    ("miniandroid/run/s27_suite/microtimer.png",                       "microtimer.png"),
    ("miniandroid/run/s27_suite/stopwatch.png",                        "stopwatch.png"),
    ("miniandroid/run/u011_matrix_recheck/simplestopwatch/screenshot.png", "simplestopwatch.png"),
    ("docs/evidence/campaign3_chessclock_real_screenshot/screenshot.png", "chessclock.png"),
    ("miniandroid/run/u011_matrix_recheck/unote/screenshot.png",       "unote.png"),
    ("miniandroid/run/master_reconciliation_apks/headingcalculator/screenshot.png", "headingcalculator.png"),
    ("miniandroid/run/master_reconciliation_apks/simplekeyboard/screenshot.png", "simplekeyboard.png"),
    ("miniandroid/run/s27_suite/dooz.png",                             "dooz_placeholder.png"),
    ("miniandroid/run/s26_sttt/screenshot.png",                        "sttt_partial.png"),
    ("miniandroid/run/s34_evidence/s34_nsp_screenshot.png",            "dooz_s34_placeholder.png"),
]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

report = []
tot_before = tot_after = 0
for src_rel, name in IMAGES:
    src = os.path.join(ROOT, src_rel)
    dst = os.path.join(OUT, name)
    im = Image.open(src).convert("RGB")
    w, h = im.size
    tw = 540
    th = round(h * tw / w)
    im2 = im.resize((tw, th), Image.LANCZOS)
    im2.save(dst, "PNG", optimize=True)
    sb, sa = os.path.getsize(src), os.path.getsize(dst)
    if sa >= sb:  # quantization grew it — keep the original bytes instead
        with open(src, "rb") as a, open(dst, "wb") as b:
            b.write(a.read())
        sa = sb
    tot_before += sb
    tot_after += sa
    report.append({
        "ledger": name,
        "source": src_rel,
        "orig_px": f"{w}x{h}",
        "new_px": f"{tw}x{th}",
        "orig_bytes": sb,
        "new_bytes": sa,
        "ratio": round(sa / sb, 3) if sb else 0,
        "src_sha256": sha256(src),
        "ledger_sha256": sha256(dst),
    })

with open(os.path.join(OUT, "ledger_images.json"), "w") as f:
    json.dump(report, f, indent=1)

print(f"{'ledger file':26} {'orig':>9} {'new':>8} {'x':>6}")
for r in report:
    print(f"{r['ledger']:26} {r['orig_bytes']//1024:>7}KB {r['new_bytes']//1024:>6}KB {r['ratio']:>6.3f}")
print("-" * 55)
print(f"TOTAL before: {tot_before/1024:.0f} KB | after: {tot_after/1024:.0f} KB | "
      f"saved: {(tot_before-tot_after)/1024:.0f} KB ({100*(1-tot_after/tot_before):.1f}% smaller)")
