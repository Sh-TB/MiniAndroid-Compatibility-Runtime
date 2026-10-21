#!/usr/bin/env python3
"""cont151_cls.py — class overview: superclass, fields, all methods w/ sizes.
Usage: cont151_cls.py <apk> <class-desc like Lrh0;> [method-glob]
Reuses cont150_disasm2.py's verified fresh-diff-chain class_data law."""
import struct, zipfile, sys

APK = sys.argv[1] if len(sys.argv) > 1 else 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
CLS = sys.argv[2] if len(sys.argv) > 2 else 'Lrh0;'
GLOB = sys.argv[3] if len(sys.argv) > 3 else ''

z = zipfile.ZipFile(APK)
dex = z.read('classes.dex')

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

str_size, str_off = struct.unpack_from('<2I', dex, 0x38)
type_size, type_off = struct.unpack_from('<2I', dex, 0x40)
proto_off = struct.unpack_from('<I', dex, 0x4C)[0]
field_size, field_off = struct.unpack_from('<2I', dex, 0x50)
meth_size, meth_off = struct.unpack_from('<2I', dex, 0x58)
class_size, class_off = struct.unpack_from('<2I', dex, 0x60)
soa = struct.unpack_from(f'<{str_size}I', dex, str_off)

def str_at(si):
    off = soa[si]; _, o = uleb(dex, off)
    return dex[o:dex.index(b"\x00", o)].decode('utf-8', 'replace')

tds = [str_at(struct.unpack_from('<I', dex, type_off + t * 4)[0]) for t in range(type_size)]
fids = []
for i in range(field_size):
    ci, ti, ni = struct.unpack_from('<HHI', dex, field_off + i * 8)
    fids.append((tds[ci], tds[ti], str_at(ni)))
mids = []
for i in range(meth_size):
    ci, pi, ni = struct.unpack_from('<HHI', dex, meth_off + i * 8)
    ret_idx = struct.unpack_from('<I', dex, proto_off + pi * 12 + 4)[0]
    mids.append((tds[ci], str_at(ni), tds[ret_idx] if ret_idx < type_size else '?'))

target = None
for i in range(class_size):
    c = struct.unpack_from('<I', dex, class_off + i * 32)[0]
    if tds[c] == CLS:
        target = struct.unpack_from('<8I', dex, class_off + i * 32)
        break
if target is None:
    print(f'class {CLS} NOT FOUND'); sys.exit(1)
_, acc, sup, ifs, srcf, anno, cdata, svals = target
print(f'class {CLS} extends {tds[sup] if sup < type_size else "?"}')
if not cdata:
    print('(no class_data)'); sys.exit(0)
p = cdata
sf_count, p = uleb(dex, p)
if_count, p = uleb(dex, p)
dm_count, p = uleb(dex, p)
vm_count, p = uleb(dex, p)
fidx = 0
statics, instances = [], []
for _ in range(sf_count):
    fd, p = uleb(dex, p); fa, p = uleb(dex, p); fidx += fd
    statics.append(fids[fidx])
fidx = 0  # each encoded_field list starts a FRESH diff chain (dex spec)
for _ in range(if_count):
    fd, p = uleb(dex, p); fa, p = uleb(dex, p); fidx += fd
    instances.append(fids[fidx])
print(f'  static fields ({len(statics)}):')
for c, t, n in statics: print(f'    {t} {n}')
print(f'  instance fields ({len(instances)}):')
for c, t, n in instances: print(f'    {t} {n}')

def parse_methods(off, cnt, is_direct, base=0):
    out = []; midx = base; p = off
    for _ in range(cnt):
        mdiff, p = uleb(dex, p)
        acc, p = uleb(dex, p)
        code_off, p = uleb(dex, p)
        midx += mdiff
        if code_off:
            out.append((midx, code_off, is_direct))
    return out, p

dm = p
methods, dm_end = parse_methods(dm, dm_count, True)
methods += parse_methods(dm_end, vm_count, False)[0]
import fnmatch
print(f'  methods ({len(methods)}):')
for midx, code_off, is_dir in methods:
    ci, pi, ni = struct.unpack_from('<HHI', dex, meth_off + midx * 8)
    ret = tds[struct.unpack_from('<I', dex, proto_off + pi * 12 + 4)[0]] if struct.unpack_from('<I', dex, proto_off + pi * 12 + 4)[0] < type_size else '?'
    name = str_at(ni)
    if GLOB and not fnmatch.fnmatch(name, GLOB): continue
    sz = 0
    if code_off:
        sz = struct.unpack_from('<I', dex, code_off + 12)[0]
    print(f'    {name} -> {ret} direct={is_dir} insns={sz}')
