#!/usr/bin/env python3
"""cont153_s0find.py — who declares S0; what method_id 11177 (Lpz0;.S0) is."""
import struct, zipfile

zf = zipfile.ZipFile('upload/canonical_apks/io.github.yamin8000.dooz_23.apk')
dex = zf.read('classes.dex')
str_size, str_off = struct.unpack_from('<2I', dex, 0x38)
type_size, type_off = struct.unpack_from('<2I', dex, 0x40)
meth_size, meth_off = struct.unpack_from('<2I', dex, 0x58)
class_size, class_off = struct.unpack_from('<2I', dex, 0x60)

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1; r |= (x & 0x7f) << s
        if not (x & 0x80): break
        s += 7
    return r, o

soa = struct.unpack_from(f'<{str_size}I', dex, str_off)
def str_at(si):
    off = soa[si]; _, o = uleb(dex, off)
    return dex[o:dex.index(b'\x00', o)].decode('utf-8', 'replace')

tds = [str_at(struct.unpack_from('<I', dex, type_off + t*4)[0]) for t in range(type_size)]
mnames = []
for k in range(meth_size):
    c, _, n = struct.unpack_from('<HHI', dex, meth_off + k*8)
    mnames.append((tds[c], str_at(n)))

s0_mids = [(i, mnames[i][0]) for i in range(meth_size) if mnames[i][1] == 'S0']
print(f'method_ids named S0 ({len(s0_mids)}): {s0_mids[:12]}')

decls = []
for i in range(class_size):
    c = struct.unpack_from('<I', dex, class_off + i*32)[0]
    cdata = struct.unpack_from('<I', dex, class_off + i*32 + 24)[0]
    if not cdata: continue
    p = cdata
    sf, p = uleb(dex, p); inf, p = uleb(dex, p)
    dm, p = uleb(dex, p); vm, p = uleb(dex, p)
    for _ in range(sf): _, p = uleb(dex, p); _, p = uleb(dex, p)
    for _ in range(inf): _, p = uleb(dex, p); _, p = uleb(dex, p)
    found = False
    midx = 0
    for _ in range(dm):
        md, p = uleb(dex, p); _, p = uleb(dex, p); _, p = uleb(dex, p)
        midx += md
        if mnames[midx][1] == 'S0': found = True
    midx = 0
    for _ in range(vm):
        md, p = uleb(dex, p); _, p = uleb(dex, p); _, p = uleb(dex, p)
        midx += md
        if mnames[midx][1] == 'S0': found = True
    if found: decls.append(tds[c])
print(f'classes DECLARING S0 ({len(decls)}): {decls[:12]}')
