#!/usr/bin/env python3
"""cont151_xref.py — whole-dex (all classes*.dex) xref for a type: new-instance,
const-class, check-cast, instance-of, new-array, filled-new-array, invoke-*,
sget/sput. Usage: cont151_xref.py <apk> <type-desc like Lrh0;>
Walks every class_data item (fresh-diff-chain law, verified cont130/cont150)."""
import struct, zipfile, sys

APK = sys.argv[1] if len(sys.argv) > 1 else 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
TGT = sys.argv[2] if len(sys.argv) > 2 else 'Lrh0;'

zf = zipfile.ZipFile(APK)
DEXES = sorted(n for n in zf.namelist() if n.startswith('classes') and n.endswith('.dex'))
sites = []
nclasses = 0

SIZES = [2]*256
for op in range(0x00, 0x13): SIZES[op] = 1
SIZES[0x1d]=1; SIZES[0x1e]=1; SIZES[0x21]=1; SIZES[0x27]=1; SIZES[0x28]=1
for op in range(0x7b, 0x90): SIZES[op] = 1
for op in range(0xb0, 0xd0): SIZES[op] = 1
SIZES[0x13]=2; SIZES[0x15]=2; SIZES[0x16]=2; SIZES[0x19]=2
SIZES[0x14]=3; SIZES[0x18]=5
for op in range(0x38,0x3e): SIZES[op]=3
SIZES[0x1a]=2; SIZES[0x1c]=2; SIZES[0x1f]=2; SIZES[0x20]=2
SIZES[0x22]=2; SIZES[0x23]=2
SIZES[0x17]=3; SIZES[0x1b]=3
SIZES[0x24]=3; SIZES[0x25]=3; SIZES[0x26]=3
SIZES[0x29]=2; SIZES[0x2a]=3; SIZES[0x2b]=3; SIZES[0x2c]=3
for op in range(0x2d,0x32): SIZES[op]=2
for op in range(0x44,0x52): SIZES[op]=2
for op in range(0x52,0x5e): SIZES[op]=2
SIZES[0x5e]=2; SIZES[0x5f]=2
for op in range(0x60,0x6e): SIZES[op]=2
for op in range(0x6e,0x73): SIZES[op]=3
for op in range(0x74,0x79): SIZES[op]=3
for op in range(0x90,0xb0): SIZES[op]=2
for op in range(0xd0,0xe3): SIZES[op]=2
SIZES[0xfa]=4; SIZES[0xfb]=4
SIZES[0xfc]=3; SIZES[0xfd]=3; SIZES[0xfe]=3; SIZES[0xff]=3

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

for DEXNAME in DEXES:
    dex = zf.read(DEXNAME)
    str_size, str_off = struct.unpack_from('<2I', dex, 0x38)
    type_size, type_off = struct.unpack_from('<2I', dex, 0x40)
    proto_off = struct.unpack_from('<I', dex, 0x4C)[0]
    field_size, field_off = struct.unpack_from('<2I', dex, 0x50)
    meth_size, meth_off = struct.unpack_from('<2I', dex, 0x58)
    class_size, class_off = struct.unpack_from('<2I', dex, 0x60)
    soa = struct.unpack_from(f'<{str_size}I', dex, str_off)

    def str_at(si, _soa=soa, _dex=dex):
        off = _soa[si]; _, o = uleb(_dex, off)
        return _dex[o:_dex.index(b"\x00", o)].decode('utf-8', 'replace')

    tds = [str_at(struct.unpack_from('<I', dex, type_off + t * 4)[0]) for t in range(type_size)]
    fids = []
    for i in range(field_size):
        ci, ti, ni = struct.unpack_from('<HHI', dex, field_off + i * 8)
        fids.append((tds[ci], tds[ti], str_at(ni)))
    mids = []
    for i in range(meth_size):
        ci, pi, ni = struct.unpack_from('<HHI', dex, meth_off + i * 8)
        mids.append((tds[ci], str_at(ni)))

    tgt = None
    for t in range(type_size):
        if tds[t] == TGT: tgt = t; break
    if tgt is None:
        continue
    tgt_mids = {i: mids[i] for i in range(meth_size) if mids[i][0] == TGT}
    tgt_fids = {i: fids[i] for i in range(field_size) if fids[i][0] == TGT}

    def parse_methods(off, cnt, base=0):
        out = []; midx = base; p = off
        for _ in range(cnt):
            mdiff, p = uleb(dex, p)
            acc, p = uleb(dex, p)
            code_off, p = uleb(dex, p)
            midx += mdiff
            if code_off: out.append((midx, code_off))
        return out, p

    for i in range(class_size):
        c = struct.unpack_from('<I', dex, class_off + i * 32)[0]
        cdata = struct.unpack_from('<I', dex, class_off + i * 32 + 24)[0]
        if not cdata: continue
        nclasses += 1
        p = cdata
        sf, p = uleb(dex, p); inf, p = uleb(dex, p)
        dm, p = uleb(dex, p); vm, p = uleb(dex, p)
        for _ in range(sf):
            _, p = uleb(dex, p); _, p = uleb(dex, p)
        for _ in range(inf):
            _, p = uleb(dex, p); _, p = uleb(dex, p)
        ml, pend = parse_methods(p, dm)
        ml += parse_methods(pend, vm)[0]
        for midx, code_off in ml:
            owner, ni = mids[midx]
            insz = struct.unpack_from('<I', dex, code_off + 12)[0]
            insns_off = code_off + 16
            pc = 0
            while pc < insz:
                if insns_off + pc*2 + 2 > len(dex):
                    break
                unit = struct.unpack_from('<H', dex, insns_off + pc*2)[0]
                if unit == 0x0100:
                    pc += struct.unpack_from('<H', dex, insns_off + pc*2 + 2)[0]*2 + 4; continue
                if unit == 0x0200:
                    pc += struct.unpack_from('<H', dex, insns_off + pc*2 + 2)[0]*4 + 2; continue
                if unit == 0x0300:
                    ew = struct.unpack_from('<H', dex, insns_off + pc*2 + 2)[0]
                    szn = struct.unpack_from('<H', dex, insns_off + pc*2 + 4)[0]
                    pc += (szn*ew + 1)//2 + 4; continue
                op = unit & 0xff
                sz = max(1, SIZES[op])
                ref = struct.unpack_from('<H', dex, insns_off + pc*2 + 2)[0] if sz >= 2 else None
                hit = None
                if op in (0x22, 0x1c, 0x1f, 0x20, 0x23) and ref == tgt:
                    hit = {0x22:'new-instance',0x1c:'const-class',0x1f:'check-cast',
                           0x20:'instance-of',0x23:'new-array'}[op]
                elif op in (0x24, 0x25) and ref == tgt:
                    hit = 'filled-new-array'
                elif op in (0x70,0x71,0x72,0x73,0x74,0x75,0x76,0x77,0x78) and ref in tgt_mids:
                    hit = f'invoke->{tgt_mids[ref][1]}'
                elif 0x60 <= op <= 0x6d and ref in tgt_fids:
                    hit = f'field->{tgt_fids[ref][2]}'
                if hit:
                    sites.append((owner, ni, hit, pc))
                pc += sz

print(f'scanned {nclasses} classes with code across {len(DEXES)} dex files; sites referencing {TGT}: {len(sites)}')
for owner, meth, kind, pc in sites[:80]:
    print(f'  {owner}.{meth} [{kind}]')
