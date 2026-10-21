#!/usr/bin/env python3
"""cont153_cleanwalk.py — CORRECT class_data walk (multi-line loops, per-list
restart). Enumerates Lpz0; methods with real names + code offsets."""
import struct, zipfile

APK = 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
zf = zipfile.ZipFile(APK)
dex = zf.read('classes.dex')
str_size, str_off = struct.unpack_from('<2I', dex, 0x38)
type_size, type_off = struct.unpack_from('<2I', dex, 0x40)
meth_size, meth_off = struct.unpack_from('<2I', dex, 0x58)
class_size, class_off = struct.unpack_from('<2I', dex, 0x60)

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1; r |= (x & 0x7f) << s
        if not (x & 0x80):
            break
        s += 7
    return r, o

soa = struct.unpack_from(f'<{str_size}I', dex, str_off)

def str_at(si):
    off = soa[si]
    _, o = uleb(dex, off)
    return dex[o:dex.index(b'\x00', o)].decode('utf-8', 'replace')

tds = [str_at(struct.unpack_from('<I', dex, type_off + t * 4)[0]) for t in range(type_size)]
mnames = []
for k in range(meth_size):
    c, _, n = struct.unpack_from('<HHI', dex, meth_off + k * 8)
    mnames.append((tds[c], str_at(n)))

import sys
TARGET = sys.argv[1] if len(sys.argv) > 1 else 'Lpz0;'

for i in range(class_size):
    c = struct.unpack_from('<I', dex, class_off + i * 32)[0]
    if tds[c] != TARGET:
        continue
    cdata = struct.unpack_from('<I', dex, class_off + i * 32 + 24)[0]
    if not cdata:
        print('no class_data')
        continue
    p = cdata
    sf, p = uleb(dex, p)
    inf, p = uleb(dex, p)
    dm, p = uleb(dex, p)
    vm, p = uleb(dex, p)
    for _ in range(sf):
        _, p = uleb(dex, p)
        _, p = uleb(dex, p)
    for _ in range(inf):
        _, p = uleb(dex, p)
        _, p = uleb(dex, p)
    for lst, cnt in (('direct', dm), ('virtual', vm)):
        midx = 0
        for _ in range(cnt):
            md, p = uleb(dex, p)
            acc, p = uleb(dex, p)
            co, p = uleb(dex, p)
            midx += md
            cls, name = mnames[midx]
            if co:
                regs = struct.unpack_from('<H', dex, co)[0]
                insz = struct.unpack_from('<I', dex, co + 12)[0]
                print(f'{lst:7s} mid={midx:6d} {cls}.{name} code_off={co} regs={regs & 0xff} ins={(regs >> 8) & 0xff} insns={insz}')
            else:
                print(f'{lst:7s} mid={midx:6d} {cls}.{name} (abstract/no-code)')
