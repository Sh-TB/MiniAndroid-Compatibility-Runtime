#!/usr/bin/env python3
"""train3 final: did the board appear? pixel probes + op census + pins."""
import struct, zlib, collections, hashlib, json, sys

OUT = "/home/z/my-project/tmp/s134_train3_out"

def png_pixels(path):
    data = open(path, "rb").read()
    pos = 8; w = h = None; idat = b""
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        chunk = data[pos+8:pos+8+ln]
        if typ == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", chunk[:10])
            ch = {0:1,2:3,3:1,4:2,6:4}[ct]
        elif typ == b"IDAT":
            idat += chunk
        pos += 12 + ln
    raw = zlib.decompress(idat)
    px = bytearray(w*h*3)
    prev = bytearray(w*ch)
    ptr = 0
    for row in range(h):
        ft = raw[ptr]; ptr += 1
        line = bytearray(raw[ptr:ptr+w*ch]); ptr += w*ch
        if ft == 1:
            for i in range(ch, len(line)): line[i] = (line[i]+line[i-ch]) & 0xFF
        elif ft == 2:
            for i in range(len(line)): line[i] = (line[i]+prev[i]) & 0xFF
        elif ft == 3:
            for i in range(len(line)):
                a = line[i-ch] if i >= ch else 0
                line[i] = (line[i]+((a+prev[i])>>1)) & 0xFF
        elif ft == 4:
            for i in range(len(line)):
                a = line[i-ch] if i >= ch else 0
                b = prev[i]; c = prev[i-ch] if i >= ch else 0
                p = a+b-c
                pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i]+pr) & 0xFF
        if ch == 3:
            px[row*w*3:(row+1)*w*3] = line
        elif ch == 4:
            for x in range(w):
                o = x*4; d = (row*w+x)*3
                for j in range(3): px[d+j] = line[o+j] if line[o+3] else 0
        elif ch == 1:
            for x in range(w):
                px[(row*w+x)*3:(row*w+x)*3+3] = bytes([line[x]]*3)
        prev = line
    return w, h, px

frames = sys.argv[1:] or ["frame_000","frame_004","frame_005","frame_006","frame_007","frame_008","frame_009","frame_010","frame_011","frame_012","frame_013"]
for name in frames:
    try:
        w,h,px = png_pixels(f"{OUT}/frames/{name}.png")
        def probe(x,y):
            o=(y*w+x)*3; return (px[o],px[o+1],px[o+2])
        zone = collections.Counter()
        for y in range(400,1500,11):
            for x in range(60,1020,11):
                zone[probe(x,y)] += 1
        top = zone.most_common(4)
        print(f"{name}: distinct={len(zone)} top={top}")
        if len(zone) > 1:
            print(f"   sha256={hashlib.sha256(open(f'{OUT}/frames/{name}.png','rb').read()).hexdigest()}")
    except Exception as e:
        print(name, "ERR", e)

# canvas op census
ops = collections.Counter(); yband = collections.Counter()
with open(f"{OUT}/canvas_ops.jsonl") as f:
    for line in f:
        t = line.split()
        if len(t) < 6: continue
        ops[t[1]] += 1
        try: y = float(t[3])
        except: continue
        if 400 <= y <= 1500:
            yband[t[1]] += 1
print("\nTOTAL OPS:", sum(ops.values()), dict(ops.most_common(8)))
print("OPS IN y:400-1500:", sum(yband.values()), dict(yband.most_common(8)))
