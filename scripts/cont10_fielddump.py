#!/usr/bin/env python3
"""cont10_fielddump.py — dump fields/methods of a class from APK dex.
Usage: cont10_fielddump.py <apk> <Ldesc;> [--methods] [--all]"""
import sys, zipfile, struct

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7f) << s; s += 7
        if not x & 0x80: return r, o

def main():
    apk, desc = sys.argv[1], sys.argv[2]
    show_methods = '--methods' in sys.argv
    all_dex = '--all' in sys.argv
    z = zipfile.ZipFile(apk)
    for dexname in [n for n in z.namelist() if n.endswith('.dex')]:
        d = z.read(dexname)
        str_size, str_off = struct.unpack_from('<II', d, 56)
        type_size, type_off = struct.unpack_from('<II', d, 64)
        field_size, field_off = struct.unpack_from('<II', d, 80)
        meth_size, meth_off = struct.unpack_from('<II', d, 88)
        class_size, class_off = struct.unpack_from('<II', d, 96)
        def getstr(i):
            o = struct.unpack_from('<I', d, str_off + 4*i)[0]
            _, p = uleb(d, o)
            e = d.index(b'\x00', p)
            return d[p:e].decode('utf-8', 'replace')
        def gettype(i):
            si = struct.unpack_from('<I', d, type_off + 4*i)[0]
            return getstr(si)
        for ci in range(class_size):
            co = class_off + 32*ci
            cdesc = gettype(struct.unpack_from('<I', d, co)[0])
            if cdesc != desc:
                if all_dex: continue
                continue
            sup = gettype(struct.unpack_from('<I', d, co+8)[0])
            print(f'== {cdesc} in {dexname}')
            print(f'   super={sup}')
            cd_off = struct.unpack_from('<I', d, co+24)[0]
            sfc, p = uleb(d, cd_off)
            infc, p = uleb(d, p)
            dmc, p = uleb(d, p)
            vmc, p = uleb(d, p)
            fidx = 0
            for _ in range(sfc):
                diff, p = uleb(d, p); fidx += diff
                acc, p = uleb(d, p)
                fo = field_off + 8*fidx
                print(f'   static {gettype(struct.unpack_from("<H", d, fo+4)[0])} {getstr(struct.unpack_from("<I", d, fo)[0])}')
            for _ in range(infc):
                diff, p = uleb(d, p); fidx += diff
                acc, p = uleb(d, p)
                fo = field_off + 8*fidx
                print(f'   field {gettype(struct.unpack_from("<H", d, fo+4)[0])} {getstr(struct.unpack_from("<I", d, fo)[0])}')
            if show_methods:
                midx = 0
                for _ in range(dmc):
                    diff, p = uleb(d, p); midx += diff
                    acc, p = uleb(d, p)
                    mo = meth_off + 8*midx
                    print(f'   [D] {getstr(struct.unpack_from("<I", d, mo)[0])}')
                midx = 0
                for _ in range(vmc):
                    diff, p = uleb(d, p); midx += diff
                    acc, p = uleb(d, p)
                    mo = meth_off + 8*midx
                    print(f'   [V] {getstr(struct.unpack_from("<I", d, mo)[0])}')
            return
        print(f'{desc} not found in {dexname}')
main()
