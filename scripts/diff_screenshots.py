#!/usr/bin/env python3
"""Characterize the pixel diff between two MiniAndroid screenshots.

Standard PNG unfiltering (types 0-4), RGB/RGBA, then per-pixel comparison.
Prints: dimensions, changed-pixel count, diff bounding box, and a coarse
row histogram of the changes so the change can be classified (layout
repositioning vs corruption) without any hand-waving.
"""
import sys, zlib, struct


def decode_png(path):
    data = open(path, "rb").read()
    pos = 8
    idat = b""
    w = h = ct = bd = None
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        if typ == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", data[pos + 8:pos + 18])
        elif typ == b"IDAT":
            idat += data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = 4 if ct == 6 else 3
    stride = w * ch
    out = bytearray(h * stride)
    prev = bytearray(stride)
    pos = 0
    for y in range(h):
        f = raw[pos]; pos += 1
        line = bytearray(raw[pos:pos + stride]); pos += stride
        for x in range(stride):
            a = line[x - ch] if x >= ch else 0
            b = prev[x]
            c = prev[x - ch] if x >= ch else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, ch, out


def main(old_path, new_path):
    w1, h1, ch1, a = decode_png(old_path)
    w2, h2, ch2, b = decode_png(new_path)
    print(f"old {w1}x{h1}, new {w2}x{h2}")
    if (w1, h1) != (w2, h2):
        print("FRAME SIZE CHANGED")
        return
    w, h, ch = w1, h1, ch1
    changed = 0
    minx, miny, maxx, maxy = w, h, -1, -1
    row_hist = {}
    for y in range(h):
        cnt = 0
        for x in range(w):
            i = y * w * ch + x * ch
            if a[i:i + ch] != b[i:i + ch]:
                changed += 1
                cnt += 1
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
        if cnt:
            row_hist[y] = cnt
    total = w * h
    print(f"changed pixels: {changed} ({100.0 * changed / total:.2f}% of frame)")
    print(f"diff bbox: x[{minx},{maxx}] y[{miny},{maxy}]")
    ys = sorted(row_hist)
    if ys:
        print(f"changed row span: {ys[0]}..{ys[-1]} across {len(ys)} rows")
        step = max(1, len(ys) // 20)
        print("row histogram (sampled):")
        for y in ys[::step]:
            print(f"  y={y}: {row_hist[y]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
