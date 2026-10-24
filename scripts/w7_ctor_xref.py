#!/usr/bin/env python3
"""w7_ctor_xref.py — W7: find every method that CONSTRUCTS/USES a target class.
Usage: w7_ctor_xref.py <apk> <Ldesc;> [--usage]
Lean scan: decodes class_data ulebs directly, resolves names ONLY for hits.
"""
import sys
import zipfile


def main():
    apk, target = sys.argv[1], sys.argv[2]
    usage = '--usage' in sys.argv
    if not target.endswith(';'):
        target += ';'

    INVOKE = {0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78}
    SIZES = [1] * 256
    for o in list(range(0x2d, 0x3e)) + list(range(0x44, 0x5e)) + \
             list(range(0x5e, 0x6e)):
        SIZES[o] = 2
    for o in range(0x6e, 0x73): SIZES[o] = 3
    SIZES[0x73] = 1
    for o in range(0x74, 0x79): SIZES[o] = 4
    SIZES[0x79] = 1; SIZES[0x7a] = 1
    for o in list(range(0x7b, 0x90)) + list(range(0xb0, 0xd0)):
        SIZES[o] = 1
    for o in list(range(0x90, 0xb0)) + list(range(0xd0, 0xd8)) + \
             list(range(0xd8, 0xe3)):
        SIZES[o] = 2
    SIZES[0x52] = SIZES[0x53] = SIZES[0x54] = 2  # iget ops 22bit (fmt 22c)

    hits = []
    with zipfile.ZipFile(apk) as z:
        dexes = [n for n in z.namelist()
                 if n.startswith('classes') and n.endswith('.dex')]
        for dname in dexes:
            b = z.read(dname)
            str_sz, str_off = int.from_bytes(b[0x38:0x3c], 'little'), \
                int.from_bytes(b[0x3c:0x40], 'little')
            type_sz, type_off = int.from_bytes(b[0x40:0x44], 'little'), \
                int.from_bytes(b[0x44:0x48], 'little')
            proto_off = int.from_bytes(b[0x4c:0x50], 'little')
            fid_sz, fid_off = int.from_bytes(b[0x50:0x54], 'little'), \
                int.from_bytes(b[0x54:0x58], 'little')
            mid_sz, mid_off = int.from_bytes(b[0x58:0x5c], 'little'), \
                int.from_bytes(b[0x5c:0x60], 'little')
            cdef_sz, cdef_off = int.from_bytes(b[0x60:0x64], 'little'), \
                int.from_bytes(b[0x64:0x68], 'little')

            scache = {}

            def s(idx):
                v = scache.get(idx)
                if v is not None:
                    return v
                if idx >= str_sz:
                    return f"@str{idx}"
                off = int.from_bytes(b[str_off + idx * 4:str_off + idx * 4 + 4],
                                     'little')
                p = off
                while b[p] & 0x80:
                    p += 1
                p += 1
                e = b.index(b'\x00', p)
                v = b[p:e].decode('utf-8', 'replace')
                scache[idx] = v
                return v

            def t(idx):
                if idx >= type_sz:
                    return f"@type{idx}"
                return s(int.from_bytes(b[type_off + idx * 4:
                                        type_off + idx * 4 + 4], 'little'))

            def meth(idx):
                o = mid_off + idx * 8
                c = int.from_bytes(b[o:o + 2], 'little')
                n = int.from_bytes(b[o + 4:o + 8], 'little')
                return t(c), s(n)

            def uleb(p):
                r = 0; sh = 0
                while True:
                    x = b[p]; p += 1
                    r |= (x & 0x7f) << sh
                    if not (x & 0x80):
                        return r, p
                    sh += 7

            for ci in range(cdef_sz):
                cd = cdef_off + ci * 32
                cls_idx = int.from_bytes(b[cd:cd + 4], 'little')
                cdata = int.from_bytes(b[cd + 24:cd + 28], 'little')
                if cdata == 0:
                    continue
                p = cdata
                st_n, p = uleb(p); in_n, p = uleb(p)
                di_n, p = uleb(p); vi_n, p = uleb(p)
                # skip fields
                fidx = 0
                for _ in range(st_n + in_n):
                    d, p = uleb(p); fidx += d
                    _, p = uleb(p)
                for kind_n in (di_n, vi_n):
                    midx = 0
                    for _ in range(kind_n):
                        d, p = uleb(p); midx += d
                        _, p = uleb(p)
                        code, p = uleb(p)
                        if not code:
                            continue
                        insns_size = int.from_bytes(b[code + 12:code + 16],
                                                    'little')
                        io = code + 16
                        pc = 0
                        while pc < insns_size:
                            o = io + pc * 2
                            w = int.from_bytes(b[o:o + 2], 'little')
                            op = b[o]
                            if w == 0x0100:  # packed-switch payload
                                ps = int.from_bytes(b[o + 2:o + 4], 'little')
                                pc += 4 + ps * 2
                                continue
                            if w == 0x0200:  # sparse-switch payload
                                ps = int.from_bytes(b[o + 2:o + 4], 'little')
                                pc += 4 + ps * 4
                                continue
                            if w == 0x0300:  # fill-array payload
                                ew = int.from_bytes(b[o + 2:o + 4], 'little')
                                el = int.from_bytes(b[o + 4:o + 8], 'little')
                                pc += 4 + (ew * el + 1) // 2
                                continue
                            sz = SIZES[op]
                            if op in INVOKE:
                                mi = int.from_bytes(b[o + 2:o + 4], 'little')
                                if mi >= mid_sz:
                                    pc += sz if sz else 1
                                    continue
                                mo = mid_off + mi * 8
                                mc = int.from_bytes(b[mo:mo + 2], 'little')
                                if t(mc) == target:
                                    mname = s(int.from_bytes(
                                        b[mo + 4:mo + 8], 'little'))
                                    is_ctor = mname == '<init>'
                                    if usage or (is_ctor and op in (0x70,
                                                                    0x76)):
                                        ccls, cname = meth(midx)
                                        hits.append((dname, ccls, cname,
                                                     mname, op))
                            if op in (0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
                                      0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b,
                                      0x0c, 0x0d):
                                sz = SIZES[op] if SIZES[op] else 1
                            pc += sz if sz else 1

    for h in hits[:100]:
        print(f"{h[0]} | {h[1]}::{h[2]} | target.{h[3]} op={h[4]:#x}")
    print(f"-- {len(hits)} hits (showing up to 100)")


if __name__ == '__main__':
    main()
