#!/usr/bin/env python3
"""s136_str_xref.py — map a string constant to the methods whose code references it.
Usage: s136_str_xref.py <apk> <substring> [substring2 ...]
Scans every classes*.dex; for each match prints <dex> <Lclass;> <method> <string>.
"""
import sys, zipfile, struct

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7f) << s; s += 7
        if not x & 0x80: return r, o

def main():
    apk = sys.argv[1]
    pats = [p.encode() for p in sys.argv[2:]]
    z = zipfile.ZipFile(apk)
    for dexname in sorted(n for n in z.namelist() if n.endswith('.dex')):
        d = z.read(dexname)
        str_size, str_off = struct.unpack_from('<II', d, 56)
        type_size, type_off = struct.unpack_from('<II', d, 64)
        proto_size, proto_off = struct.unpack_from('<II', d, 72)
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
        def getmeth(i):
            cls, proto, nm = struct.unpack_from('<HHH', d, meth_off + 8*i)
            return gettype(cls), getstr(nm)

        # string index for each pattern
        wanted = {}
        for i in range(str_size):
            s = getstr(i)
            for p in pats:
                if p in s.encode('utf-8', 'replace'):
                    wanted[i] = s
        if not wanted:
            continue

        # walk class_def entries -> class_data -> methods w/ code
        for ci in range(class_size):
            off = class_off + 32*ci
            (cidx, acc, sfc, itf, sdi, anoff, cdoff, svoff) = struct.unpack_from('<8I', d, off)
            cls = gettype(cidx)
            if cdoff == 0: continue
            p = cdoff
            sf, p = uleb(d, p)
            inf, p = uleb(d, p)
            dm, p = uleb(d, p)
            vm, p = uleb(d, p)
            for _ in range(sf):
                _, p = uleb(d, p); _, p = uleb(d, p)
            for _ in range(inf):
                _, p = uleb(d, p); _, p = uleb(d, p)
            for _ in range(dm):
                mi, p = uleb(d, p)
                acc, p = uleb(d, p)
                co, p = uleb(d, p)
                if co:
                    code_off = struct.unpack_from('<I', d, co + 8)[0]
                    insns = struct.unpack_from('<I', d, code_off + 12)[0]
                    body = d[code_off+16:code_off+16+insns*2]
                    for j in range(0, len(body)-3, 2):
                        op = body[j+1]
                        if op == 0x1a:  # const-string
                            sidx = struct.unpack_from('<H', body, j+2)[0]
                            if sidx in wanted:
                                print(f"{dexname} {cls} (direct) -> {wanted[sidx]!r}")
                        elif op == 0x1b:  # const-string/jumbo
                            sidx = struct.unpack_from('<I', body, j+2)[0]
                            if sidx in wanted:
                                print(f"{dexname} {cls} (direct) -> {wanted[sidx]!r}")
            for _ in range(vm):
                mi, p = uleb(d, p)
                acc, p = uleb(d, p)
                co, p = uleb(d, p)
                if co:
                    code_off = struct.unpack_from('<I', d, co + 8)[0]
                    insns = struct.unpack_from('<I', d, code_off + 12)[0]
                    body = d[code_off+16:code_off+16+insns*2]
                    for j in range(0, len(body)-3, 2):
                        op = body[j+1]
                        if op == 0x1a:
                            sidx = struct.unpack_from('<H', body, j+2)[0]
                            if sidx in wanted:
                                print(f"{dexname} {cls} -> {wanted[sidx]!r}")
                        elif op == 0x1b:
                            sidx = struct.unpack_from('<I', body, j+2)[0]
                            if sidx in wanted:
                                print(f"{dexname} {cls} -> {wanted[sidx]!r}")

if __name__ == '__main__':
    main()
