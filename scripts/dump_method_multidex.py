#!/usr/bin/env python3
"""Dump a method's bytecode words from all classesN.dex (minimal DEX walker).
MASTER-3 forensics: ground-truth app semantics before any law fix.
Usage: dump_method_multidex.py <apk> <class-desc> <method-name>"""
import struct, zipfile, sys, re

apk, cls_want, meth_want = sys.argv[1], sys.argv[2], sys.argv[3]
z = zipfile.ZipFile(apk)
dex_names = sorted(n for n in z.namelist() if re.match(r'classes\d*\.dex$', n))

OPCODES = {
    0x6e: 'invoke-virtual', 0x6f: 'invoke-super', 0x70: 'invoke-direct',
    0x71: 'invoke-static', 0x72: 'invoke-interface',
    0x74: 'invoke-virtual/range', 0x75: 'invoke-super/range',
    0x76: 'invoke-direct/range', 0x77: 'invoke-static/range',
    0x78: 'invoke-interface/range',
    0x0a: 'move-result', 0x0c: 'move-result-object', 0x0b: 'move-result-wide',
    0x12: 'const/4', 0x13: 'const/16', 0x14: 'const', 0x1a: 'const-string',
    0x52: 'iget', 0x54: 'iget-object', 0x5b: 'iput', 0x5f: 'sget', 0x62: 'sget-object',
    0x6f: 'invoke-super', 0x15: 'const/high16', 0x16: 'const-wide/16',
}

def parse_dex(d, label):
    u4 = lambda o: struct.unpack_from('<I', d, o)[0]
    u2 = lambda o: struct.unpack_from('<H', d, o)[0]
    u1 = lambda o: d[o]
    str_off, type_off, m_off = u4(0x3c), u4(0x44), u4(0x5c)
    c_off, c_sz, t_sz, s_sz = u4(0x64), u4(0x60), u4(0x40), u4(0x38)
    proto_off, field_off = u4(0x6c), u4(0x54)

    def uleb(p):
        r = 0; s = 0
        while True:
            b = u1(p + s); r |= (b & 0x7f) << (7 * s); s += 1
            if not (b & 0x80):
                return r, p + s

    def get_str(idx):
        if idx >= s_sz: return '<bad_str:%d>' % idx
        off = u4(str_off + 4 * idx)
        r, p2 = uleb(off)
        if p2 + r > len(d): return '<bad_data>'
        return d[p2:p2 + r].split(b'\x00')[0].decode('utf-8', 'replace')

    def get_type(idx):
        if idx >= t_sz: return '<bad_type>'
        return get_str(u4(type_off + 4 * idx))

    def get_meth(idx):
        if idx * 8 + 8 > len(d): return ('<bad_meth>', '')
        m = u4(m_off + 8 * idx)
        return (get_type(u2(m_off + 8 * idx + 2)),  # class
                get_str(u2(m + 4) if m else 0))     # name (rough)

    def get_field(idx):
        f = u4(field_off + 8 * idx) if idx * 8 + 8 <= len(d) else 0
        return (get_type(u2(field_off + 8 * idx + 2)),
                get_str(u2(f + 4) if f else 0))

    for i in range(c_sz):
        off = c_off + 32 * i
        cname = get_type(u4(off))
        if cname != cls_want: continue
        print(f'=== {label} class {cname} ===')
        cd_off = u4(off + 24)
        if cd_off == 0: print('  (no class_data)'); continue
        p = cd_off
        sf, inf, dm, vm, _ = (uleb(p)[0], *uleb(p)[0:0], ) if False else (0,0,0,0)
        sf, p = uleb(p); inf, p = uleb(p); dm, p = uleb(p); vm, p = uleb(p)
        # static fields
        for _ in range(sf):
            _, p = uleb(p); _, p = uleb(p)
        for _ in range(inf):
            _, p = uleb(p); _, p = uleb(p)
        def methods(n, p, kind):
            midx = 0
            for _ in range(n):
                d_idx, p = uleb(p); acc, p = uleb(p)
                midx += d_idx
                moff = u4(m_off + 8 * midx)
                mname = get_str(u2(moff + 4))
                if mname != meth_want:
                    # still need to skip code_item if direct/virtual with code
                    # (we can't easily skip without parsing; re-scan approach: parse all)
                    pass
                yield midx, mname, acc, p
                # skip over the encoded_method (we must advance manually below)
            return
        # Simpler: re-walk direct methods decoding entries, capture code_off
        def walk_methods(n, p):
            midx = 0
            out = []
            for _ in range(n):
                d_idx, p = uleb(p); acc, p = uleb(p)
                midx += d_idx
                moff = u4(m_off + 8 * midx)
                mname = get_str(u2(moff + 4))
                proto_idx = u2(moff + 0)
                out.append((midx, mname, acc, p))
                # skip code_item if ACC_NATIVE/ACC_ABSTRACT not set: need code_off
                # encoded method is followed by code_off ONLY in class_data? No —
                # code_off comes from the method's code_item via table; we must
                # parse it from p BEFORE advancing… actually class_data entries
                # do NOT contain code_off. We just collect (midx,name,acc).
            return out
        dm_list = walk_methods(dm, p)
        # advance p past direct methods encoded entries
        def skip_methods(n, p):
            for _ in range(n):
                _, p = uleb(p); _, p = uleb(p)
            return p
        p = skip_methods(dm, p)
        vm_list = walk_methods(vm, p)
        for midx, mname, acc in dm_list + vm_list:
            moff = u4(m_off + 8 * midx)
            print(f'\n--- {mname} (method_idx={midx}) ---')
            # find code_item: we need the map/tables — use the runtime dump instead:
            # use code_item discovery via the dex's method -> code offset is not
            # in class_data; but Android packs it in the class_def's class_data
            # only as accessibility flags. So scan code_item list is complex here;
            # instead we print the method_ref info the engine uses:
            proto_idx = u2(moff + 2) if False else 0
        # Fallback: dump ALL invoke sites referencing formatTime anywhere
    return

for n in dex_names:
    d = z.read(n)
    # search for class name string in this dex quickly
    if cls_want.encode() in d:
        parse_dex(d, n)
