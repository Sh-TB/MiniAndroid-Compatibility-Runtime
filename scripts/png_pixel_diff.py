#!/usr/bin/env python3
"""png_pixel_diff.py — per-row pixel diff of two PNGs (pure stdlib).
Usage: png_pixel_diff.py <base.png> <after.png>"""
import struct
import sys
import zlib
from collections import Counter


def read_png(p):
    d = open(p, 'rb').read()
    pos = 8
    w = h = ch = None
    idat = b''
    while pos < len(d):
        ln = struct.unpack('>I', d[pos:pos + 4])[0]
        typ = d[pos + 4:pos + 8]
        if typ == b'IHDR':
            w, h, bd, ct = struct.unpack('>IIBB', d[pos + 8:pos + 18])
            ch = 3 if ct == 2 else (4 if ct == 6 else None)
        elif typ == b'IDAT':
            idat += d[pos + 8:pos + 8 + ln]
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * ch
    out = bytearray()
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
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
        out += line
        prev = line
    return w, h, ch, bytes(out)


def main():
    b = read_png(sys.argv[1])
    a = read_png(sys.argv[2])
    w, h, ch = b[0], b[1], b[2]
    bb, ab = b[3], a[3]
    diff_rows = Counter()
    n = 0
    for i in range(0, min(len(bb), len(ab)), ch):
        if bb[i:i + ch] != ab[i:i + ch]:
            n += 1
            y = (i // ch) // w
            diff_rows[y] += 1
    rows = sorted(diff_rows)
    print('diff pixels:', n)
    if rows:
        print('rows:', rows[0], 'to', rows[-1])
        print('max diffs in one row:', max(diff_rows.values()))
        # top 5 diff rows
        for y, c in sorted(diff_rows.items(), key=lambda kv: -kv[1])[:5]:
            print(f'  row y={y}: {c} px')


if __name__ == '__main__':
    main()
