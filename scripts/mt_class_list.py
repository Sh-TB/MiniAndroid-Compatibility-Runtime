#!/usr/bin/env python3
"""mt_class_list.py — list classes (and optional method filter) in a DEX.
Usage: python3 mt_class_list.py <apk> [method_or_class_substr ...]
"""
import struct, zipfile, sys

apk = sys.argv[1]
pats = [p for p in sys.argv[2:]]
z = zipfile.ZipFile(apk)
names = z.namelist()
dexes = [n for n in names if n.startswith('classes') and n.endswith('.dex')]
d = z.read('classes.dex')

def u4(o): return struct.unpack_from('<I', d, o)[0]
def u2(o): return struct.unpack_from('<H', d, o)[0]

str_off, str_sz = u4(0x3c), u4(0x38)
type_off = u4(0x44)
meth_off, meth_sz = u4(0x5c), u4(0x58)
cls_off, cls_sz = u4(0x64), u4(0x60)

def uleb(p):
    r, s = 0, 0
    while True:
        b = d[p + s]; r |= (b & 0x7f) << (7 * s); s += 1
        if not (b & 0x80): return r, p + s

def gs(i):
    if i >= str_sz: return '<str:%d>' % i
    off = u4(str_off + 4 * i); r, p = uleb(off)
    return d[p:p + r].split(b'\x00')[0].decode('utf-8', 'replace')

def gt(i): return gs(u4(type_off + 4 * i))

for ci in range(cls_sz):
    off = cls_off + 32 * ci
    tn = gt(u4(off))
    if pats and not any(p.lower() in tn.lower() for p in pats):
        continue
    cdo = u4(off + 24)
    print(tn)
    if pats:
        # list methods
        if cdo:
            p = cdo
            sf, p = uleb(p); iff, p = uleb(p); dm, p = uleb(p); vm, p = uleb(p)
            for _ in range(sf + iff):
                _, p = uleb(p); _, p = uleb(p)
            midx = 0
            for _ in range(dm + vm):
                d1, p = uleb(p); d2, p = uleb(p); d3, p = uleb(p); midx += d1
                if midx < meth_sz and d3:
                    print('    %s' % gs(u4(meth_off + 8 * midx + 4)))
