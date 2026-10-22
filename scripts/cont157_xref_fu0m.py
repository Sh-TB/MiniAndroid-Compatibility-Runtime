#!/usr/bin/env python3
"""cont157_xref_fu0m.py — find every method that invokes Lfu0;->m (and optionally other targets).
Scan all code items for invoke ops whose BBBB == target mid; verify by disasm."""
import struct, zipfile, sys

APK = 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
TARGET_CLASS = 'Lyl;'
TARGET_NAME = 'D'

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

d = zipfile.ZipFile(APK).read('classes.dex')
str_size, str_off = struct.unpack_from('<2I', d, 0x38)
type_size, type_off = struct.unpack_from('<2I', d, 0x40)
proto_size, proto_off = struct.unpack_from('<2I', d, 0x48)
field_size, field_off = struct.unpack_from('<2I', d, 0x50)
meth_size, meth_off = struct.unpack_from('<2I', d, 0x58)
class_size, class_off = struct.unpack_from('<2I', d, 0x60)
soa = struct.unpack_from(f'<{str_size}I', d, str_off)
def str_at(si):
    off = soa[si]; _, o = uleb(d, off)
    return d[o:d.index(b'\x00', o)].decode('utf-8', 'replace')
tds = [str_at(struct.unpack_from('<I', d, type_off + t*4)[0]) for t in range(type_size)]
mids = [(tds[c], str_at(n), p) for c, p, n in
        (struct.unpack_from('<HHI', d, meth_off + i*8) for i in range(meth_size))]

target_mid = None
for i, (c, n, p) in enumerate(mids):
    if c == TARGET_CLASS and n == TARGET_NAME:
        target_mid = i; break
print(f'target {TARGET_CLASS}->{TARGET_NAME} mid={target_mid}')

classes = {}
for i in range(class_size):
    cidx, acc, sup, ifo, src, ann, cd_off, stv = struct.unpack_from('<8I', d, class_off + i*32)
    classes[tds[cidx]] = (cd_off, tds[sup] if sup != 0xffffffff else None)

SIZES = [2]*256
for op in range(0x00, 0x08): SIZES[op] = 1
SIZES[0x0f]=1; SIZES[0x10]=1; SIZES[0x11]=1; SIZES[0x12]=1
SIZES[0x08]=2; SIZES[0x09]=2; SIZES[0x0a]=1; SIZES[0x0e]=1
SIZES[0x0b]=1; SIZES[0x0c]=1; SIZES[0x0d]=1
SIZES[0x1d]=1; SIZES[0x1e]=1; SIZES[0x21]=1; SIZES[0x27]=1; SIZES[0x28]=1
for op in range(0x7b, 0x90): SIZES[op] = 1
for op in range(0xb0, 0xd0): SIZES[op] = 1
SIZES[0x13]=2; SIZES[0x15]=2; SIZES[0x16]=2; SIZES[0x19]=2
SIZES[0x14]=3; SIZES[0x18]=5
for op in range(0x38,0x3e): SIZES[op]=2
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

def scan_insns(insns, want):
    """Return pcs where an invoke references a wanted mid (verified by stepper)."""
    hits = []
    i = 0; n = len(insns)
    while i < n:
        w = insns[i]; op = w & 0xff
        if w == 0x0100:
            sz = insns[i+1] if i+1 < n else 0; i += 4 + sz*2; continue
        if w == 0x0200:
            sz = insns[i+1] if i+1 < n else 0; i += 2 + sz*4; continue
        if w == 0x0300:
            ew = insns[i+1] if i+1 < n else 0
            sz = (insns[i+2] | (insns[i+3]<<16)) if i+3 < n else 0
            i += 4 + (sz*ew + 1)//2; continue
        if 0x6e <= op <= 0x78 and i+1 < n:
            mi = insns[i+1] & 0xffff
            if mi == want:
                hits.append(i)
        i += SIZES[op]
    return hits

hits_total = 0
for desc, (cd_off, sup) in classes.items():
    if not cd_off: continue  # class_data_off == 0 → no class_data (dex spec)
    o = cd_off
    try:
        sf, o = uleb(d, o); inf, o = uleb(d, o); dm, o = uleb(d, o); vm, o = uleb(d, o)
    except IndexError:
        continue
    idx = 0
    for _ in range(sf):
        _, o = uleb(d, o); _, o = uleb(d, o)
    idx = 0
    for _ in range(inf):
        _, o = uleb(d, o); _, o = uleb(d, o)
    for kind, cnt in (('direct', dm), ('virtual', vm)):
        idx = 0
        for _ in range(cnt):
            diff, o = uleb(d, o); acc, o = uleb(d, o); code_off, o = uleb(d, o); idx += diff
            if not code_off: continue
            try:
                insns_sz = struct.unpack_from('<I', d, code_off + 12)[0]
                insns = struct.unpack_from(f'<{insns_sz}H', d, code_off + 16)
            except struct.error:
                continue
            for pc in scan_insns(insns, target_mid):
                hits_total += 1
                if idx < len(mids):
                    mc, mn, mp = mids[idx]
                    print(f'XREF: {desc}->{mn} (mid {idx}) calls {TARGET_CLASS}->{TARGET_NAME} at pc={pc}')
                else:
                    print(f'XREF: {desc} (bad idx {idx}) calls {TARGET_CLASS}->{TARGET_NAME} at pc={pc}')
print(f'total xrefs: {hits_total}')
