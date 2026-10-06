#!/usr/bin/env python3
"""cont7w2_field_rw.py — find all readers/writers of an instance field (iget/iput)
Usage: cont7w2_field_rw.py <apk> <class> <field>
"""
import sys, zipfile, struct

APK = sys.argv[1]
CLS = sys.argv[2]
FLD = sys.argv[3]

if APK.endswith('.dex'):
    b = open(APK, 'rb').read()
else:
    z = zipfile.ZipFile(APK); b = z.read('classes.dex')

SIZES = [1]*256
for o in range(0x01,0x0a): SIZES[o]=1
for o in range(0x0a,0x13): SIZES[o]=1
SIZES[0x13]=2; SIZES[0x14]=3; SIZES[0x15]=2
SIZES[0x16]=2; SIZES[0x17]=3; SIZES[0x18]=5; SIZES[0x19]=2
SIZES[0x1a]=2; SIZES[0x1b]=3; SIZES[0x1c]=2
SIZES[0x1d]=1; SIZES[0x1e]=1
SIZES[0x1f]=2; SIZES[0x20]=2; SIZES[0x21]=1; SIZES[0x22]=2; SIZES[0x23]=2
SIZES[0x24]=3; SIZES[0x25]=3; SIZES[0x26]=3
SIZES[0x27]=1
SIZES[0x28]=1; SIZES[0x29]=2; SIZES[0x2a]=3
SIZES[0x2b]=3; SIZES[0x2c]=3
for o in range(0x2d,0x32): SIZES[o]=2
for o in range(0x32,0x3e): SIZES[o]=2
for o in range(0x3e,0x44): SIZES[o]=1
for o in range(0x44,0x52): SIZES[o]=2
for o in range(0x52,0x5e): SIZES[o]=2
for o in range(0x5e,0x6e): SIZES[o]=2
for o in range(0x6e,0x73): SIZES[o]=3
SIZES[0x73]=1
for o in range(0x74,0x79): SIZES[o]=4
for o in range(0x7b,0x90): SIZES[o]=1
for o in range(0x90,0xb0): SIZES[o]=2
for o in range(0xb0,0xd0): SIZES[o]=1
for o in range(0xd0,0xd8): SIZES[o]=2
for o in range(0xd8,0xe3): SIZES[o]=2
SIZES[0xfa]=4; SIZES[0xfb]=4; SIZES[0xfc]=3; SIZES[0xfd]=3

def uleb(off):
    r = 0; s = 0
    while True:
        by = b[off]; off += 1
        r |= (by & 0x7f) << s
        if not (by & 0x80): break
        s += 7
    return r, off

string_ids_size, string_ids_off = struct.unpack_from('<II', b, 56)
type_ids_size, type_ids_off = struct.unpack_from('<II', b, 64)
field_ids_size, field_ids_off = struct.unpack_from('<II', b, 80)
method_ids_size, method_ids_off = struct.unpack_from('<II', b, 88)
class_defs_size, class_defs_off = struct.unpack_from('<II', b, 96)

def gs(i):
    do, = struct.unpack_from('<I', b, string_ids_off + i*4)
    n, off = uleb(do)
    e = b.index(b'\x00', off)
    return b[off:e].decode('utf-8', 'replace')

def gt(i):
    si, = struct.unpack_from('<I', b, type_ids_off + i*4)
    return gs(si)

# target field ids
targets = {}
for i in range(field_ids_size):
    cls, typ, name = struct.unpack_from('<HHI', b, field_ids_off + i*8)
    if gt(cls) == CLS and gs(name) == FLD:
        targets[i] = ('W' if 'put' in '' else '', None)
print(f"target field_ids: {list(targets)}", file=sys.stderr)

def parse_cd(off):
    sf, off = uleb(off); inf, off = uleb(off)
    dm, off = uleb(off); vm, off = uleb(off)
    for _ in range(sf):
        _, off = uleb(off); _, off = uleb(off)
    for _ in range(inf):
        _, off = uleb(off); _, off = uleb(off)
    out = []
    midx = 0
    for _ in range(dm):
        d, off = uleb(off); midx += d
        acc, off = uleb(off); coff, off = uleb(off)
        out.append(('direct', midx, acc, coff))
    midx = 0
    for _ in range(vm):
        d, off = uleb(off); midx += d
        acc, off = uleb(off); coff, off = uleb(off)
        out.append(('virtual', midx, acc, coff))
    return out

IGET = set(range(0x52, 0x58))  # iget family reads
IPUT = set(range(0x59, 0x5f))  # iput family writes

for ci in range(class_defs_size):
    off = class_defs_off + ci*32
    cls_idx, access, superclass, interfaces_off, src, ann, class_data, sv = struct.unpack_from('<8I', b, off)
    if class_data == 0:
        continue
    cls = gt(cls_idx)
    for kind, midx, acc, coff in parse_cd(class_data):
        if coff == 0:
            continue
        regs, ins, outs, tries, dbg, insns_size = struct.unpack_from('<HHHHII', b, coff)
        insns_off = coff + 16
        pc = 0
        hits = []
        while pc < insns_size:
            u0, = struct.unpack_from('<H', b, insns_off + pc*2)
            op = u0 & 0xff
            if u0 == 0x0100:
                size, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
                pc += 4 + 2*size; continue
            if u0 == 0x0200:
                size, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
                pc += 2 + 4*size; continue
            if u0 == 0x0300:
                ew, size = struct.unpack_from('<HH', b, insns_off + (pc+1)*2)
                pc += 4 + (size*ew + 1)//2; continue
            if op in range(0x52, 0x5e):
                f, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
                if f in targets:
                    hits.append((pc, 'READ' if op in IGET else 'WRITE'))
                pc += 2; continue
            if op in range(0x6e, 0x73) or op in range(0x74, 0x79):
                pc += SIZES[op]; continue
            if op in (0x2b, 0x2c):
                pc += 3; continue
            pc += SIZES[op]
        if hits:
            try:
                c2, p2, n2 = struct.unpack_from('<HHI', b, method_ids_off + midx*8)
                mname = gs(n2)
            except Exception:
                mname = f"midx={midx}"
            print(f"{cls} ({kind}) .{mname}  {hits}")
