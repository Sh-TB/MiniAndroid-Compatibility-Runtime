#!/usr/bin/env python3
"""CONT-11 W7 train-3 analysis: did the tap make the board issue ops?"""
import json, hashlib, collections, struct, zlib, sys

OUT = "/home/z/my-project/tmp/s134_train3_out"

# 1) canvas op census
ops = collections.Counter()
yband = collections.Counter()
band_ops = []
with open(f"{OUT}/canvas_ops.jsonl") as f:
    for line in f:
        try:
            d = json.loads(line)
        except Exception:
            continue
        op = d.get("op") or d.get("name") or d.get("kind") or "?"
        ops[op] += 1
        # y coordinate: try common fields
        y = None
        for k in ("y", "top", "y0"):
            if k in d and isinstance(d[k], (int, float)):
                y = d[k]; break
        if y is None and "rect" in d:
            try:
                y = d["rect"][1]
            except Exception:
                pass
        if y is not None and 400 <= y <= 1500:
            yband[op] += 1
            if len(band_ops) < 8:
                band_ops.append({k: d[k] for k in list(d)[:6]})
print("TOTAL OPS:", sum(ops.values()))
print("BY OP:", dict(ops.most_common(12)))
print("OPS IN y:400-1500:", sum(yband.values()), dict(yband.most_common(8)))
for b in band_ops[:5]:
    print("  sample:", json.dumps(b)[:160])

# 2) crash log
try:
    print("\n=== crash.log:")
    print(open(f"{OUT}/crash.log").read()[:900])
except Exception as e:
    print("crash.log:", e)

# 3) sha256 pins (ZERO-LOG: hashes only)
for name in ("screenshot.png",):
    h = hashlib.sha256(open(f"{OUT}/{name}", "rb").read()).hexdigest()
    print(f"\nsha256({name}) = {h}")

# 4) pixel probes of board zone
def png_pixels(path):
    data = open(path, "rb").read()
    pos = 8; w = h = None; idat = b""
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        chunk = data[pos+8:pos+8+ln]
        if typ == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", chunk[:10])
        elif typ == b"IDAT":
            idat += chunk
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * 3 + 1  # assume 8-bit RGB
    px = bytearray(w * h * 3)
    prev = bytearray(w * 3)
    ptr = 0
    for row in range(h):
        ft = raw[ptr]; ptr += 1
        line = bytearray(raw[ptr:ptr + w*3]); ptr += w*3
        if ft == 1:
            for i in range(3, len(line)): line[i] = (line[i] + line[i-3]) & 0xFF
        elif ft == 2:
            for i in range(len(line)): line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(len(line)):
                a = line[i-3] if i >= 3 else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(len(line)):
                a = line[i-3] if i >= 3 else 0
                b = prev[i]
                c = prev[i-3] if i >= 3 else 0
                p = a + b - c
                pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        px[row*w*3:(row+1)*w*3] = line
        prev = line
    return w, h, px

try:
    w, h, px = png_pixels(f"{OUT}/screenshot.png")
    def probe(x, y):
        o = (y*w + x)*3
        return (px[o], px[o+1], px[o+2])
    # board zone: grid cell centers predicted: box area 42..1038 x, y ~400..1500
    # 3x3 cells: cell size ~ (996 - 2*margin)/3; margin Medium ~ 42? sample grid centers:
    pts = {
        "board_center(540,950)": (540, 950),
        "cell_r0c0": (200, 550),
        "cell_r1c1": (540, 950),
        "cell_r2c2": (880, 1350),
        "gap_h(540,730)": (540, 730),
        "topbar_title(488,98)": (488, 98),
        "newgame(765,1830)": (765, 1830),
    }
    print("\n=== pixel probes (RGB):")
    for k, (x, y) in pts.items():
        print(f"  {k}: {probe(x, y)}")
    # distinct colors in board zone
    cols = collections.Counter()
    for y in range(400, 1500, 7):
        for x in range(60, 1020, 7):
            cols[probe(x, y)] += 1
    print("distinct colors in board zone (sampled):", len(cols), "top5:", cols.most_common(5))
except Exception as e:
    print("pixel probe error:", e)
