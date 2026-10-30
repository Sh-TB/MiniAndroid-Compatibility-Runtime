#!/usr/bin/env python3
"""cont11_fieldscan.py — raw-scan DEX code items for iget/iput/sget/sput of a field.
Usage: cont11_fieldscan.py <apk> <Lcls;> <fieldname> [max]
Per-class independent parse; misparsed classes are skipped (census semantics)."""
import sys, zipfile, struct

def uleb(d, o):
    r = 0; s = 0
    while True:
        x = d[o]; o += 1
        r |= (x & 0x7f) << s; s += 7
        if not x & 0x80: return r, o

def sleb(d, o):
    r = 0; s = 0
    while True:
        x = d[o]; o += 1
        r |= (x & 0x7f) << s; s += 7
        if not x & 0x80:
            if x & 0x40: r -= 1 << s
            return r, o

FIELD_OPS = {0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f,
             0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d}

def main():
    apk, tcls, tfld = sys.argv[1], sys.argv[2], sys.argv[3]
    maxr = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    z = zipfile.ZipFile(apk)
    hits = {}
    for name in [n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]:
        d = z.read(name)
        str_size, str_off = struct.unpack_from('<II', d, 56)
        type_size, type_off = struct.unpack_from('<II', d, 64)
        field_size, field_off = struct.unpack_from('<II', d, 80)
        class_size, class_off = struct.unpack_from('<II', d, 96)
        def getstr(i):
            o = struct.unpack_from('<I', d, str_off + 4*i)[0]
            _, p = uleb(d, o)
            e = d.index(b'\x00', p)
            return d[p:e].decode('utf-8', 'replace')
        def gettype(i):
            return getstr(struct.unpack_from('<I', d, type_off + 4*i)[0])
        fidx = None
        for i in range(field_size):
            cls_i, typ_i, nam_i = struct.unpack_from('<HHI', d, field_off + 8*i)
            if gettype(cls_i) == tcls and getstr(nam_i) == tfld:
                fidx = i; break
        if fidx is None:
            continue
        for ci in range(class_size):
            coff = class_off + 32*ci
            cname = gettype(struct.unpack_from('<I', d, coff)[0])
            fo = struct.unpack_from('<I', d, coff+24)[0]
            if fo == 0: continue
            try:
                o = fo
                sf, o = uleb(d, o); inf, o = uleb(d, o)
                dm, o = uleb(d, o); vm, o = uleb(d, o)
                def skip_fields(o, n):
                    for _ in range(n):
                        _, o = uleb(d, o)
                        _, o = uleb(d, o)
                    return o
                o = skip_fields(o, sf)
                o = skip_fields(o, inf)
                def walk_methods(o, n):
                    for _ in range(n):
                        _, o = uleb(d, o)
                        _, o = uleb(d, o)
                        co, o = uleb(d, o)
                        if not co:
                            continue
                        reg, ins, outs, tries, dbg, inz = struct.unpack_from('<HHHHII', d, co)
                        insns_off = co + 16
                        code = d[insns_off:insns_off + inz*2]
                        for j in range(0, len(code)-1, 2):
                            op = code[j+1]
                            if op in FIELD_OPS:
                                fi = struct.unpack_from('<H', code, j+2)[0]
                                if fi == fidx:
                                    hits[cname] = hits.get(cname, 0) + 1
                        if tries:
                            tail = insns_off + inz*2
                            if tail & 3:
                                tail += 2
                            tail += tries * 12
                            hcount, tail = uleb(d, tail)
                            for _ in range(hcount):
                                hsize, tail = sleb(d, tail)
                                cnt = hsize if hsize >= 0 else -hsize
                                for _h in range(cnt):
                                    _, tail = uleb(d, tail)
                                    _, tail = uleb(d, tail)
                                if hsize <= 0:
                                    _, tail = uleb(d, tail)
                            o = tail
                o = walk_methods(o, dm)
                o = walk_methods(o, vm)
            except Exception:
                continue
        break
    for k, v in sorted(hits.items(), key=lambda kv: -kv[1])[:maxr]:
        print(v, k)
    if not hits:
        print("NO-HITS", tcls, tfld)

if __name__ == '__main__':
    main()
