#!/usr/bin/env python3
"""cont7w2_callers.py — find all callers of a given class.method in a DEX.
Usage: cont7w2_callers.py <apk> <class> <method> [proto_substring]
"""
import sys, zipfile, struct

APK = sys.argv[1]
CLS = sys.argv[2]
METH = sys.argv[3]
PROTOSUB = sys.argv[4] if len(sys.argv) > 4 else None

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
proto_ids_size, proto_ids_off = struct.unpack_from('<II', b, 72)
field_ids_size, field_ids_off = struct.unpack_from('<II', b, 80)
method_ids_size, method_ids_off = struct.unpack_from('<II', b, 88)
class_defs_size, class_defs_off = struct.unpack_from('<II', b, 96)

def get_string(i):
    do, = struct.unpack_from('<I', b, string_ids_off + i*4)
    n, off = uleb(do)
    e = b.index(b'\x00', off)
    return b[off:e].decode('utf-8', 'replace')

def get_type(i):
    si, = struct.unpack_from('<I', b, type_ids_off + i*4)
    return get_string(si)

def get_proto(i):
    shorty, ret_t, params = struct.unpack_from('<III', b, proto_ids_off + i*12)
    ret = get_type(ret_t)
    ps = ''
    if params:
        poff, = struct.unpack_from('<I', b, params)
        if poff:
            psz, = struct.unpack_from('<I', b, poff)
            o2 = poff + 4
            for _ in range(psz):
                ti, = struct.unpack_from('<H', b, o2)
                ps += get_type(ti)
                o2 += 2
    return f"({ps}){ret}"

def get_method(i):
    cls, proto, name = struct.unpack_from('<HHI', b, method_ids_off + i*8)
    return f"{get_type(cls)}.{get_string(name)}{get_proto(proto)}", get_type(cls), get_string(name)

# find target method ids
target_mids = []
for i in range(method_ids_size):
    cls, proto, name = struct.unpack_from('<HHI', b, method_ids_off + i*8)
    try:
        tn = get_string(name)
        tc = get_type(cls)
    except Exception:
        continue
    if tc == CLS and tn == METH:
        try:
            pr = get_proto(proto)
        except Exception:
            pr = '?'
        if PROTOSUB is None or PROTOSUB in pr:
            target_mids.append(i)
print(f"target method_ids: {target_mids}", file=sys.stderr)
if not target_mids:
    sys.exit(1)
tset = set(target_mids)

def parse_class_data(off):
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

found = 0
for ci in range(class_defs_size):
    off = class_defs_off + ci*32
    cls_idx, access, superclass, interfaces_off, src, ann, class_data, sv = struct.unpack_from('<8I', b, off)
    if class_data == 0:
        continue
    cls = get_type(cls_idx)
    for kind, midx, acc, coff in parse_class_data(class_data):
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
            if op in range(0x6e, 0x73) or op in range(0x74, 0x79):
                m, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
                if m in tset:
                    hits.append(pc)
                pc += SIZES[op]
                continue
            if op in (0x2b, 0x2c):
                pc += 3; continue
            if op in (0x1a, 0x1c, 0x1f, 0x22):
                pc += 2; continue
            pc += SIZES[op]
        if hits:
            found += 1
            m0 = None
            for i2 in range(method_ids_size):
                c2, p2, n2 = struct.unpack_from('<HHI', b, method_ids_off + midx*8)
            try:
                full, _, _ = get_method(midx)
            except Exception:
                full = f"midx={midx}"
            print(f"caller: {cls} ({kind}) {full}  pcs={hits}")

print(f"\nTOTAL caller methods: {found}")
