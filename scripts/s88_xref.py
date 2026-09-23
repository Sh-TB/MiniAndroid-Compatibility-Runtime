#!/usr/bin/env python3
"""s88_xref.py — find methods referencing a string in an APK's dexes.
Usage: s88_xref.py <apk> <substring>  → lists <class>.<method> hits."""
import sys, zipfile, struct, io, re

def uleb(f):
    r = 0; s = 0
    while True:
        b = f.read(1)[0]
        r |= (b & 0x7f) << s
        s += 7
        if not b & 0x80: break
    return r

apk = sys.argv[1]
pat = sys.argv[2].encode()
z = zipfile.ZipFile(apk)
for name in [n for n in z.namelist() if n.endswith('.dex')]:
    d = z.read(name)
    ssz, sof = struct.unpack_from('<II', d, 0x38)
    tsz, tof = struct.unpack_from('<II', d, 0x40)
    psz, pof = struct.unpack_from('<II', d, 0x48)
    fsz, fof = struct.unpack_from('<II', d, 0x50)
    msz, mof = struct.unpack_from('<II', d, 0x58)

    def string(i):
        off = struct.unpack_from('<I', d, sof + i*4)[0]
        f = io.BytesIO(d); f.seek(off)
        n = uleb(f)
        return f.read(n).decode('utf-8', 'replace')

    def tdesc(i):
        return string(struct.unpack_from('<I', d, tof + i*4)[0])

    def proto(i):
        pi, ri, si = struct.unpack_from('III', d, pof + i*12)
        return string(si), tdesc(ri)

    # find string idx
    sidx = [i for i in range(ssz) if pat in string(i).encode()]
    if not sidx:
        continue
    for want in sidx:
        # find methods whose code contains const-string referencing want
        cdsz, cdof = struct.unpack_from('<II', d, 0x60)
        for c in range(cdsz):
            off = cdof + c*32
            cidx = struct.unpack_from('<I', d, off)[0]
            coff = struct.unpack_from('<I', d, off+24)[0]
            if coff == 0:
                continue
            f = io.BytesIO(d); f.seek(coff)
            sf = uleb(f); inf = uleb(f); dm = uleb(f); vm = uleb(f)
            fidx = 0
            for _ in range(sf):
                fidx += uleb(f); uleb(f)
            for _ in range(inf):
                fidx += uleb(f); uleb(f)
            cls_desc = tdesc(cidx)
            midx = 0
            for _ in range(dm + vm):
                midx += uleb(f); acc = uleb(f)
                mi = midx
                code_off = uleb(f)
                mid_off = mof + mi*16
                cidx2, pidx, nidx = struct.unpack_from('<HHI', d, mid_off)
                if code_off == 0 or code_off > len(d) - 16:
                    continue
                regsz, insz, outsz, triesz, dbg, insns_sz, insns_off = \
                    struct.unpack_from('<HHHHIII', d, code_off)
                if insns_off > len(d) - insns_sz*2: continue
                raw = struct.unpack_from('<%dH' % insns_sz, d, insns_off)
                pc = 0
                hit = False
                while pc < insns_sz:
                    op = raw[pc] & 0xFF
                    if op == 0x1a:  # const-string
                        bidx = raw[pc+1] if pc+1 < len(raw) else -1
                        if bidx == want:
                            hit = True; break
                    elif op == 0x1b:  # const-string/jumbo
                        bidx = raw[pc+1] if pc+1 < len(raw) else -1 | (raw[pc+2] << 16)
                        if bidx == want:
                            hit = True; break
                    sz = 1
                    if op in (0x12,0x13,0x1a): sz = 2
                    elif op in (0x22,0x6e,0x6f,0x70,0x71,0x72,0x1b,0x1c,0x54,0x59): sz = 3
                    elif op in (0x2b,0x2c,0x26,0x74,0x75,0x76,0x77,0x78): sz = 3
                    pc += sz
                if hit:
                    sname, _ = None, None
                    print(f"{name}: {cls_desc}.{string(struct.unpack_from('<HHI', d, mid_off)[2])}")
