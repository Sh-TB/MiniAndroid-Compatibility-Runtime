#!/usr/bin/env python3
"""cont7w3_instof_xref.py — find all methods containing instance-of / check-cast
on a given type. Usage: cont7w3_instof_xref.py <apk> Landroid/os/Bundle; [--callee]
"""
import sys, zipfile, struct

APK = sys.argv[1]
TYPE = sys.argv[2]
OPNAMES = {0x1c: 'const-class', 0x1f: 'check-cast', 0x20: 'instance-of',
           0x21: 'array-length', 0x22: 'new-instance', 0x23: 'new-array',
           0x24: 'filled-new-array', 0x25: 'filled-new-array/range', 0x27: 'throw'}

S = [1]*256
S[0x01]=1; S[0x02]=2; S[0x03]=3   # move, move/from16, move/16
S[0x04]=1; S[0x05]=2; S[0x06]=3   # move-wide family
S[0x07]=1; S[0x08]=2; S[0x09]=3   # move-object family
for o in range(0x0a, 0x13): S[o] = 1
S[0x12] = 1
S[0x13] = 2; S[0x14] = 3; S[0x15] = 2; S[0x16] = 2; S[0x17] = 3; S[0x18] = 5; S[0x19] = 2
S[0x1a] = 2; S[0x1b] = 3; S[0x1c] = 2
S[0x1d] = 1; S[0x1e] = 1
S[0x1f] = 2; S[0x20] = 2; S[0x21] = 1; S[0x22] = 2; S[0x23] = 2
S[0x24] = 3; S[0x25] = 3; S[0x26] = 3
S[0x27] = 1
S[0x28] = 1; S[0x29] = 2; S[0x2a] = 3
S[0x2b] = 3; S[0x2c] = 3
for o in range(0x2d, 0x32): S[o] = 2
for o in range(0x32, 0x3e): S[o] = 2
for o in range(0x44, 0x52): S[o] = 2
for o in range(0x52, 0x5e): S[o] = 2
for o in range(0x5e, 0x6e): S[o] = 2
for o in range(0x6e, 0x73): S[o] = 3
S[0x73] = 1
for o in range(0x74, 0x79): S[o] = 4
for o in range(0x7b, 0x90): S[o] = 1
for o in range(0x90, 0xb0): S[o] = 2
for o in range(0xb0, 0xd0): S[o] = 1
for o in range(0xd0, 0xd8): S[o] = 2
for o in range(0xd8, 0xe3): S[o] = 2
S[0xfa] = 4; S[0xfb] = 4; S[0xfc] = 3; S[0xfd] = 3

if APK.endswith('.dex'):
    b = open(APK, 'rb').read()
else:
    b = zipfile.ZipFile(APK).read('classes.dex')

def uleb(off):
    r = 0; s = 0
    while True:
        by = b[off]; off += 1
        r |= (by & 0x7f) << s; s += 7
        if not by & 0x80: return r, off

string_ids_size, string_ids_off = struct.unpack_from('<II', b, 0x38)
type_ids_size, type_ids_off = struct.unpack_from('<II', b, 0x40)
method_ids_size, method_ids_off = struct.unpack_from('<II', b, 0x58)
class_defs_size, class_defs_off = struct.unpack_from('<II', b, 0x60)

def getstr(i):
    off = struct.unpack_from('<I', b, string_ids_off + 4*i)[0]
    l, off = uleb(off)
    return b[off:b.index(b'\x00', off)].decode('utf-8', 'replace')

def gettype(i):
    if i == 0xffffffff: return '<none>'
    return getstr(struct.unpack_from('<I', b, type_ids_off + 4*i)[0])

tidx = next(i for i in range(type_ids_size) if gettype(i) == TYPE)

def getmethod(i):
    ci, pi, ni = struct.unpack_from('<HHI', b, method_ids_off + 8*i)
    return gettype(ci), getstr(ni), getstr(struct.unpack_from('<I', b, b.index(b'\x00', 0) + 0) [0] if False else proto_off_pi(pi))

def proto_off(pi):
    # proto_ids: 12 bytes each: shorty_idx, return_type_idx, parameters_off
    return struct.unpack_from('<I', b, 0x48 + 0 + 0)[0]  # placeholder

# simpler: read proto params for signature
proto_ids_off = struct.unpack_from('<I', b, 0x4c)[0]
def meth_sig(i):
    ci, pi, ni = struct.unpack_from('<HHI', b, method_ids_off + 8*i)
    _, rt, poff = struct.unpack_from('<HHI', b, proto_ids_off + 12*pi)
    if poff and poff + 4 <= len(b):
        n = struct.unpack_from('<I', b, poff)[0]
        if 0 < n < 64 and poff + 4 + 2*n <= len(b):
            ps = [gettype(t) for t in struct.unpack_from(f'<{n}H', b, poff+4)]
        else:
            ps = []
    else:
        ps = []
    return f"{gettype(ci)}.{getstr(ni)}({','.join(ps)}){gettype(rt)}"

hits = []
for ci in range(class_defs_size):
    coff = class_defs_off + ci*32
    cls_idx, access, superclass, interfaces_off, srcf, ann, class_data_off, sval = \
        struct.unpack_from('<8I', b, coff)
    cls = gettype(cls_idx)
    if not class_data_off: continue
    p = class_data_off
    sf, p = uleb(p); ifc, p = uleb(p); dmc, p = uleb(p); vmc, p = uleb(p)
    for _ in range(sf):
        _, p = uleb(p); _, p = uleb(p)
    for _ in range(ifc):
        _, p = uleb(p); _, p = uleb(p)
    for section, count in (('direct', dmc), ('virtual', vmc)):
        prev = 0
        for _ in range(count):
            d, p = uleb(p); a, p = uleb(p)
            midx = prev + d; prev = midx
            c2, p = uleb(p)
            code_off = c2
            if not code_off or code_off + 16 > len(b):
                continue
            regs, ins, outs, tries, dbg, insns_size = struct.unpack_from('<HHHHII', b, code_off)
            ip = code_off + 16
            end = ip + insns_size*2
            if end > len(b):
                continue
            seq = []
            while ip < end:
                op = b[ip]
                if op in (0x1c, 0x1f, 0x20, 0x22, 0x23):
                    ti = struct.unpack_from('<H', b, ip+2)[0]
                    if ti == tidx:
                        seq.append((ip - code_off - 16, OPNAMES[op]))
                elif op == 0x27:
                    seq.append((ip - code_off - 16, 'throw'))
                sz = S[op]
                ip += sz*2
            if seq and any(n != 'throw' for _, n in seq):
                hits.append((cls, section, meth_sig(midx), code_off, seq))

for cls, section, sig, coff, seq in hits:
    pcs = ', '.join(f'{n}@pc{pc}' for pc, n in seq)
    print(f"{cls} [{section}] {sig} (code@{coff}): {pcs}")
print(f"TOTAL: {len(hits)} methods reference {TYPE}")
