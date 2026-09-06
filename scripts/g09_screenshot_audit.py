#!/usr/bin/env python3
"""g09_screenshot_audit.py — pixel-content audit of every corpus screenshot.
Distinguishes REAL rendered UI from blank windows (AppCompat/Compose shell).
"""
import json
import struct
import zlib
from pathlib import Path
from collections import Counter

WORK = Path("/tmp/g09_runs")
RESULTS = Path(__file__).resolve().parents[1] / \
    "docs/evidence/g09_corpus/results"


def read_png_pixels(path: Path):
    """Minimal PNG reader (8-bit RGB/RGBA, non-interlaced)."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, w, h, bitd, ctype = 8, b"", 0, 0, 0, 0
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bitd, ctype = struct.unpack(">IIBB", chunk[:10])
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"IEND":
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    stride = w * ch
    # un-filter
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    px = bytearray()
    for i in range(0, len(out), ch):
        if ch >= 3:
            px += out[i:i + 3]
        else:
            g = out[i]
            px += bytes((g, g, g))
    return w, h, px


def audit(path: Path) -> dict:
    w, h, px = read_png_pixels(path)
    n = w * h
    colors = Counter(px[i:i + 3].hex() for i in range(0, len(px), 3))
    top = colors.most_common(3)
    bg = top[0]
    nonbg = n - bg[1]
    return {
        "file": str(path), "w": w, "h": h,
        "unique_colors": len(colors),
        "background_rgb": bytes.fromhex(bg[0]).hex(":"),
        "background_share": round(bg[1] / n, 4),
        "nonbg_pixels": nonbg,
        "nonbg_share": round(nonbg / n, 5),
        "top_colors": [{"rgb": bytes.fromhex(c).hex(":"),
                        "share": round(s / n, 4)} for c, s in top],
    }


def main() -> None:
    report = {}
    for d in sorted(WORK.iterdir()):
        if not d.is_dir():
            continue
        entry = {}
        shot = d / "base/screenshot.png"
        if shot.exists():
            entry["base"] = audit(shot)
        for f in sorted((d / "click").glob("click_frame_*.png")):
            entry.setdefault("click_frames", {})[f.name] = audit(f)
        report[d.name] = entry
        b = entry.get("base")
        if b:
            print(f"{d.name:45s} colors={b['unique_colors']:6d} "
                  f"nonbg={b['nonbg_share']:8.5f} bg={b['background_rgb']}")
    (RESULTS / "g09_screenshot_audit.json").write_text(
        json.dumps(report, indent=2) + "\n")
    print(f"→ {RESULTS/'g09_screenshot_audit.json'}")


if __name__ == "__main__":
    main()
