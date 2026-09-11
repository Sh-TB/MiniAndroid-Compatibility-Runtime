#!/usr/bin/env python3
"""Forensic: prove screenshot.png pixels == raw framebuffer screenshot.ppm
and report PPM header facts. No fabrication: pure byte comparison."""
import sys, struct, zlib

def read_ppm(path):
    d = open(path, 'rb').read()
    # P6 header: magic, width, height, maxval, single whitespace, then raster
    assert d[:2] == b'P6', 'not P6'
    parts = []
    i = 2
    while len(parts) < 3:
        while i < len(d) and d[i] in b' \t\r\n':
            i += 1
        if d[i:i+1] == b'#':
            while d[i] not in b'\r\n':
                i += 1
            continue
        j = i
        while j < len(d) and d[j] not in b' \t\r\n':
            j += 1
        parts.append(int(d[i:j])); i = j
    i += 1  # single whitespace after maxval
    w, h, mx = parts
    raster = d[i:]
    assert len(raster) == w*h*3, 'raster size mismatch: %d vs %d' % (len(raster), w*h*3)
    return w, h, mx, raster

def png_pixels(path):
    data = open(path, 'rb').read()
    w, h = struct.unpack('>II', data[16:24])
    pos = 8; idat = b''
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        if typ == b'IDAT':
            idat += data[pos+8:pos+8+ln]
        if typ == b'IEND':
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w*3
    out = bytearray(); prev = bytearray(stride); i = 0
    for y in range(h):
        ft = raw[i]; i += 1
        line = bytearray(raw[i:i+stride]); i += stride
        if ft == 1:
            for x in range(3, stride): line[x] = (line[x]+line[x-3]) & 0xFF
        elif ft == 2:
            for x in range(stride): line[x] = (line[x]+prev[x]) & 0xFF
        elif ft == 3:
            for x in range(stride):
                a = line[x-3] if x >= 3 else 0
                line[x] = (line[x]+((a+prev[x])>>1)) & 0xFF
        elif ft == 4:
            for x in range(stride):
                a = line[x-3] if x >= 3 else 0
                b = prev[x]; c = prev[x-3] if x >= 3 else 0
                p = a+b-c
                pa,pb,pc = abs(p-a),abs(p-b),abs(p-c)
                pr = a if (pa<=pb and pa<=pc) else (b if pb<=pc else c)
                line[x] = (line[x]+pr) & 0xFF
        out += line; prev = line
    return w, h, bytes(out)

if __name__ == '__main__':
    ppm = sys.argv[1]; png = sys.argv[2]
    w1,h1,mx,raster = read_ppm(ppm)
    w2,h2,pix = png_pixels(png)
    print('PPM: %dx%d maxval=%d raster=%d bytes' % (w1,h1,mx,len(raster)))
    print('PNG decoded: %dx%d pixels=%d bytes' % (w2,h2,len(pix)))
    same = (w1==w2 and h1==h2 and raster==pix)
    diff = sum(1 for a,b in zip(raster,pix) if a!=b) if not same else 0
    print('PIXEL-IDENTICAL:', same, ('differing bytes=%d' % diff) if not same else '')
