#!/usr/bin/env python3
"""cont159_xref.py — find every method that invokes a target method (whole-DEX xref).
Usage: cont159_xref.py <apk> <target-class-desc> <target-method-name> [proto-prefix-filter]"""
import struct, zipfile, sys

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

APK = sys.argv[1]
TCLASS = sys.argv[2]
TNAME = sys.argv[3]
TPROTO = sys.argv[4] if len(sys.argv) > 4 else None

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

def proto_str(pi):
    ret_idx = struct.unpack_from('<I', d, proto_off + pi*12 + 4)[0]
    poff = struct.unpack_from('<I', d, proto_off + pi*12 + 8)[0]
    ret = tds[ret_idx]
    params = ''
    if poff:
        cnt = struct.unpack_from('<I', d, poff)[0]
        params = ''.join(tds[p] for p in struct.unpack_from(f'<{cnt}H', d, poff+4))
    return params, ret

mids = [(tds[c], str_at(n), p) for c, p, n in
        (struct.unpack_from('<HHI', d, meth_off + i*8) for i in range(meth_size))]

# target method ids
targets = [i for i, (c, n, p) in enumerate(mids) if c == TCLASS and n == TNAME]
if TPROTO and TPROTO.startswith('id='):
    targets = [int(TPROTO[3:], 16)]
print(f'target method ids: {[hex(t) for t in targets]}')
tset = set(targets)

classes = {}
for i in range(class_size):
    cidx, acc, sup, ifo, src, ann, cd_off, stv = struct.unpack_from('<8I', d, class_off + i*32)
    classes[tds[cidx]] = cd_off

def walk_class(desc, cd_off):
    o = cd_off
    sf, o = uleb(d, o); inf, o = uleb(d, o); dm, o = uleb(d, o); vm, o = uleb(d, o)
    idx = 0
    for _ in range(inf):
        diff, o = uleb(d, o); acc, o = uleb(d, o)
    idx = 0
    for _ in range(sf):
        diff, o = uleb(d, o); acc, o = uleb(d, o)
    for kind, cnt in (('direct', dm), ('virtual', vm)):
        idx = 0
        for _ in range(cnt):
            diff, o = uleb(d, o); acc, o = uleb(d, o); code_off, o = uleb(d, o); idx += diff
            if not code_off: continue
            mc, mn, mp = mids[idx]
            full = f'{mc}->{mn}({proto_str(mp)[0]}){proto_str(mp)[1]}'
            reg, insz, outs, tries = struct.unpack_from('<4H', d, code_off)
            insns_sz = struct.unpack_from('<I', d, code_off + 12)[0]
            insns = struct.unpack_from(f'<{insns_sz}H', d, code_off + 16)
            for i, w in enumerate(insns):
                op = w & 0xff
                if 0x6e <= op <= 0x78 and i + 2 < insns_sz:
                    bc = insns[i+1]
                    if (bc & 0xffff) in tset:
                        hit = mids[bc & 0xffff]
                        print(f'{full}  ({"static-inv" if op==0x71 else "invoke"}) unit-pc={i}')

for desc, cd_off in classes.items():
    if not cd_off: continue
    try:
        walk_class(desc, cd_off)
    except Exception:
        pass
