#!/usr/bin/env python3
"""PNG pixel analyzer (S60 evidence gate) — non-black ratio + color census."""
import zlib, struct, sys

def analyze(path):
    data = open(path, 'rb').read()
    pos = 8
    w = h = 0
    idat = b''
    channels = 3
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        if typ == b'IHDR':
            w, h = struct.unpack('>II', data[pos+8:pos+16])
            bd, ct = data[pos+16], data[pos+17]
            channels = {0:1, 2:3, 3:1, 4:2, 6:4}.get(ct, 3)
            assert bd == 8, f'bit depth {bd}'
        elif typ == b'IDAT':
            idat += data[pos+8:pos+8+ln]
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * channels + 1
    colors = {}
    nonblack = 0
    total = 0
    for y in range(0, h, 7):
        row = raw[y*stride+1:(y+1)*stride]
        for x in range(0, w*channels, channels*3):
            px = bytes(row[x:x+channels])
            total += 1
            if px != b'\x00' * channels:
                nonblack += 1
            colors[px] = colors.get(px, 0) + 1
    print(f'{path}: {w}x{h} non-black={nonblack/total:.4f} distinct={len(colors)}')
    for c, n in sorted(colors.items(), key=lambda kv: -kv[1])[:5]:
        print('   ', c.hex(), n)

for p in sys.argv[1:]:
    analyze(p)
