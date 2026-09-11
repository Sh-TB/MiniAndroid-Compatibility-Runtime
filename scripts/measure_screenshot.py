#!/usr/bin/env python3
"""Measure a real runtime screenshot: resolution, non-white pixel count, SHA-256.
No fabrication: reads the PNG the runtime actually wrote."""
import sys, hashlib, struct, zlib

def measure(path):
    with open(path, 'rb') as f:
        data = f.read()
    sha = hashlib.sha256(data).hexdigest()
    # parse PNG IHDR
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'not a PNG'
    w, h = struct.unpack('>II', data[16:24])
    bitdepth, colortype = data[24], data[25]
    # decode IDAT
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
    channels = {0:1, 2:3, 3:1, 4:2, 6:4}[colortype]
    stride = w * channels
    bpp = channels
    # unfilter
    out = bytearray()
    prev = bytearray(stride)
    i = 0
    for y in range(h):
        ft = raw[i]; i += 1
        line = bytearray(raw[i:i+stride]); i += stride
        if ft == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x-bpp]) & 0xFF
        elif ft == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 0xFF
        elif ft == 3:
            for x in range(stride):
                a = line[x-bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 0xFF
        elif ft == 4:
            for x in range(stride):
                a = line[x-bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x-bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 0xFF
        out += line
        prev = line
    # non-white count (pixel is non-white if any channel < 255)
    nonwhite = 0
    px = w * h
    if colortype in (2, 6):
        alpha_ignored = (colortype == 6)
        for p in range(px):
            o = p * channels
            if out[o] != 255 or out[o+1] != 255 or out[o+2] != 255:
                nonwhite += 1
    elif colortype == 0:
        for p in range(px):
            if out[p] != 255:
                nonwhite += 1
    else:
        print('colortype %d needs palette handling' % colortype); sys.exit(2)
    print('path=%s' % path)
    print('resolution=%dx%d' % (w, h))
    print('total_pixels=%d' % (w*h))
    print('nonwhite_pixel_count=%d' % nonwhite)
    print('sha256=%s' % sha)
    print('file_size=%d' % len(data))
    print('colortype=%d bitdepth=%d' % (colortype, bitdepth))

if __name__ == '__main__':
    measure(sys.argv[1])
