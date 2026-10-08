#!/usr/bin/env python3
"""cont11_flatxref.py — flat u16-pattern scan for references to a target class.
No instruction walk (desync-proof). Over-approximates; verify hits by disasm.
Usage: cont11_flatxref.py <apk> <Ldesc;>
"""
import sys, zipfile, struct

apk = sys.argv[1]
target = sys.argv[2]

zf = zipfile.ZipFile(apk)

def parse_dex(dexname, data):
    def u4(off): return struct.unpack_from('<I', data, off)[0]
    def u2(off): return struct.unpack_from('<H', data, off)[0]
    string_ids_size = u4(0x38); string_ids_off = u4(0x3c)
    type_ids_size = u4(0x40); type_ids_off = u4(0x44)
    proto_ids_off = u4(0x4c); field_ids_off = u4(0x54)
    method_ids_size = u4(0x58); method_ids_off = u4(0x5c)
    class_defs_size = u4(0x60); class_defs_off = u4(0x64)

    def get_string(idx):
        off = u4(string_ids_off + 4*idx)
        n = 0; s = 0; p = off
        while True:
            b = data[p]; n |= (b & 0x7f) << s; s += 7; p += 1
            if not (b & 0x80): break
        raw = data[p:p+n]
        out = []; i = 0
        while i < len(raw):
            c = raw[i]
            if c == 0: break
            if c < 0x80: out.append(chr(c)); i += 1
            elif c < 0xe0: out.append(chr(((c & 0x1f) << 6) | (raw[i+1] & 0x3f))); i += 2
            else: out.append(chr(((c & 0x0f) << 12) | ((raw[i+1] & 0x3f) << 6) | (raw[i+2] & 0x3f))); i += 3
        return ''.join(out)

    def type_str(idx): return get_string(u4(type_ids_off + 4*idx))

    # target type_idx
    ttype = None
    for i in range(type_ids_size):
        if type_str(i) == target:
            ttype = i
            break
    if ttype is None:
        return []

    # method_ids of the target class
    tmethods = {}
    for i in range(method_ids_size):
        off = method_ids_off + 8*i
        if type_str(u2(off)) == target:
            tmethods[i] = get_string(u4(off+4))
    tfields = {}
    for i in range(u4(0x50) if False else 0, 0):
        pass
    # field_ids
    field_ids_size = u4(0x50)
    for i in range(field_ids_size):
        off = field_ids_off + 8*i
        if type_str(u2(off)) == target:
            tfields[i] = get_string(u4(off+4))

    def method_info(idx):
        off = method_ids_off + 8*idx
        cls = type_str(u2(off)); name = get_string(u4(off+4))
        return cls, name

    # map class_def -> class_data code spans (method -> [insns_off, insns_size])
    spans = []  # (cls_desc, mname, mdesc, insns_off_bytes, insns_size_units)
    for ci in range(class_defs_size):
        coff = class_defs_off + 32*ci
        cls_desc = type_str(u4(coff))
        class_data_off = u4(coff + 24)
        if class_data_off == 0: continue
        p = class_data_off
        def uleb():
            nonlocal p
            r = 0; s = 0
            while True:
                b = data[p]; r |= (b & 0x7f) << s; s += 7; p += 1
                if not (b & 0x80): break
            return r
        sf = uleb(); iff = uleb(); dm = uleb(); vm = uleb()
        for _ in range(sf): uleb(); uleb()
        for _ in range(iff): uleb(); uleb()
        midx = 0
        for kind, count in (('D', dm), ('V', vm)):
            midx = 0  # each list restarts its diff base
            for _ in range(count):
                diff = uleb(); _acc = uleb(); code_off = uleb()
                midx += diff
                if code_off == 0: continue
                mc, mn = method_info(midx)
                insns_size = u4(code_off + 12)
                insns_off = code_off + 16
                spans.append((cls_desc, f'{mn}', insns_off, insns_size))

    hits = []
    for cls_desc, mname, insns_off, nunits in spans:
        for k in range(nunits - 1):
            unit = u2(insns_off + 2*k)
            op = unit & 0xff
            nxt = u2(insns_off + 2*(k+1))
            if op == 0x22 and nxt == ttype:      # new-instance
                hits.append((cls_desc, mname, hex(k*2), f'new-instance {target}'))
            elif op == 0x1c and nxt == ttype:    # const-class
                hits.append((cls_desc, mname, hex(k*2), f'const-class {target}'))
            elif op == 0x1f and nxt == ttype:    # check-cast
                hits.append((cls_desc, mname, hex(k*2), f'check-cast {target}'))
            elif op == 0x20 and nxt == ttype:    # instance-of
                hits.append((cls_desc, mname, hex(k*2), f'instance-of {target}'))
            elif op in (0x6e,0x6f,0x70,0x71,0x72,0x74,0x75,0x76,0x77,0x78) and nxt in tmethods:
                m = tmethods[nxt]
                names = {0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
                         0x71:'invoke-static',0x72:'invoke-interface',0x74:'invoke-virtual/range',
                         0x75:'invoke-super/range',0x76:'invoke-direct/range',
                         0x77:'invoke-static/range',0x78:'invoke-interface/range'}
                hits.append((cls_desc, mname, hex(k*2), f'{names[op]} {target}-> {m}'))
            elif op in range(0x52, 0x6a) and nxt in tfields:
                hits.append((cls_desc, mname, hex(k*2), f'field-ref {target}.{tfields[nxt]}'))
    return hits

total = 0
for dn in sorted(n for n in zf.namelist() if n.startswith('classes') and n.endswith('.dex')):
    for h in parse_dex(dn, zf.read(dn)):
        print(dn, *h)
        total += 1
print('TOTAL', total)
