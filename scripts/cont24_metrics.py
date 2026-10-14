#!/usr/bin/env python3
"""cont24_metrics.py — SKEL-LIGHT experiment frame metrics.
Usage: cont24_metrics.py <screenshot.png>  -> prints JSON one-liner."""
import hashlib, json, struct, sys, zlib, collections


def png_metrics(path):
    with open(path, "rb") as f:
        data = f.read()
    sha = hashlib.sha256(data).hexdigest()
    w = h = 0
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", data[16:24])
    idat = b""
    i = 8
    while i < len(data):
        ln = struct.unpack(">I", data[i:i+4])[0]
        typ = data[i+4:i+8]
        if typ == b"IDAT":
            idat += data[i+8:i+8+ln]
        i += 12 + ln
    raw = zlib.decompress(idat)
    # infer channel count from IHDR byte 8+8+1 (color type at offset 25)
    ctype = data[25]
    bpp = 4 if (ctype & 4) else 3
    stride = w * bpp + 1
    # unfilter (Paeth/sub/up/average) — full honest decode
    prev = bytearray(w * bpp)
    out = bytearray()
    pos = 0
    for _ in range(h):
        ft = raw[pos]
        row = bytearray(raw[pos+1:pos+stride])
        pos += stride
        if ft == 1:
            for j in range(bpp, len(row)):
                row[j] = (row[j] + row[j-bpp]) & 0xFF
        elif ft == 2:
            for j in range(len(row)):
                row[j] = (row[j] + prev[j]) & 0xFF
        elif ft == 3:
            for j in range(len(row)):
                a = row[j-bpp] if j >= bpp else 0
                row[j] = (row[j] + ((a + prev[j]) >> 1)) & 0xFF
        elif ft == 4:
            for j in range(len(row)):
                a = row[j-bpp] if j >= bpp else 0
                b = prev[j]
                c = prev[j-bpp] if j >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[j] = (row[j] + pr) & 0xFF
        prev = row
        out += row
    colors = collections.Counter()
    total = 0
    for y in range(0, h, 3):          # 1/9 sampling like cont19
        base = y * w * bpp
        for x in range(0, w, 3):
            o = base + x * bpp
            colors[(out[o], out[o+1], out[o+2])] += 1
            total += 1
    dom, dom_n = colors.most_common(1)[0] if colors else ((0, 0, 0), 0)
    return {
        "sha16": sha[:16],
        "colors": len(colors),
        "dominant": "#%02x%02x%02x" % dom,
        "dom_share": round(dom_n / max(total, 1), 4),
        "nondom": total - dom_n,
        "w": w, "h": h,
    }


if __name__ == "__main__":
    print(json.dumps(png_metrics(sys.argv[1])))
