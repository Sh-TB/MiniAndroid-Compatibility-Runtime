#!/usr/bin/env python3
"""s136_pixel_probe.py — minimal PNG RGB probe for board presence.
Usage: s136_pixel_probe.py <frame.png> [frame2.png ...]
Prints per-frame distinct-color counts in board band / fab zone / title band.
"""
import zlib, struct, sys

def pixels(p):
    d = open(p, 'rb').read()
    pos = 8; w = h = 0; idat = b''
    while pos < len(d):
        ln, = struct.unpack_from('>I', d, pos); typ = d[pos+4:pos+8]
        if typ == b'IHDR':
            w, h, bd, ct = struct.unpack_from('>IIBB', d, pos+8)
        if typ == b'IDAT':
            idat += d[pos+8:pos+8+ln]
        pos += 12 + ln
    if ct == 6:
        bpp = 4
    elif ct == 2:
        bpp = 3
    else:
        print(p, 'colortype', ct, 'not supported'); return None
    raw = zlib.decompress(idat)
    stride = w*bpp + 1
    px = bytearray(); prev = bytearray(w*bpp); o = 0
    for y in range(h):
        f = raw[o]; o += 1
        line = bytearray(raw[o:o+w*bpp]); o += w*bpp
        if f == 1:
            for i in range(bpp, len(line)): line[i] = (line[i]+line[i-bpp]) & 255
        elif f == 2:
            for i in range(len(line)): line[i] = (line[i]+prev[i]) & 255
        elif f == 3:
            for i in range(len(line)):
                a = line[i-bpp] if i >= bpp else 0
                line[i] = (line[i]+((a+prev[i])>>1)) & 255
        elif f == 4:
            for i in range(len(line)):
                a = line[i-bpp] if i >= bpp else 0
                b = prev[i]; c = prev[i-bpp] if i >= bpp else 0
                pp = a+b-c; pa, pb, pc = abs(pp-a), abs(pp-b), abs(pp-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i]+pr) & 255
        prev = line; px += line
    return w, h, px, bpp

def probe(p):
    r = pixels(p)
    if not r: return
    w, h, px, bpp = r
    zones = {'board': (60, 1020, 400, 1500), 'fab': (500, 1030, 1750, 1900),
             'title': (0, 1080, 0, 300)}
    out = []
    for name, (x0, x1, y0, y1) in zones.items():
        y1 = min(y1, h); x1 = min(x1, w)
        cols = {}
        for y in range(y0, y1, 7):
            for x in range(x0, x1, 7):
                i = (y*w+x)*bpp; c = px[i:i+3]
                k = '#%02x%02x%02x' % (c[0], c[1], c[2])
                cols[k] = cols.get(k, 0) + 1
        top = sorted(cols.items(), key=lambda kv: -kv[1])[:4]
        out.append(f"{name}: distinct={len(cols)} top={top}")
    print(p.split('/')[-1], ' | '.join(out))

for a in sys.argv[1:]:
    probe(a)
