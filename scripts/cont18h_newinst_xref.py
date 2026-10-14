#!/usr/bin/env python3
"""cont18h_newinst_xref.py — find all new-instance sites of a given type in a DEX.

Usage: cont18h_newinst_xref.py <apk_or_dex> <Lcls;>

SOURCE-FIRST tool for the F-265 arm-(c) investigation: which methods
construct a class (so we can check whether the engine ran their <init>).
Walks every class_def -> class_data -> code_item, decodes the instruction
stream with the standard opcode-size table (offset-accurate for 22b/35c
formats which carry the type_idx in the operands we care about).
"""
import sys, zipfile, struct

APK = sys.argv[1]
CLS = sys.argv[2]

if APK.endswith('.dex'):
    b = open(APK, 'rb').read()
else:
    z = zipfile.ZipFile(APK)
    b = z.read('classes.dex')

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

def get_string(i):
    off = struct.unpack_from('<I', b, string_ids_off + 4 * i)[0]
    n, off = uleb(off)
    e = b.index(b'\x00', off)
    return b[off:e].decode('utf8', 'replace')

def get_type(i):
    return get_string(struct.unpack_from('<I', b, type_ids_off + 4 * i)[0])

def get_field(i):
    class_idx, type_idx, name_idx = struct.unpack_from('<HHI', b, field_ids_off + 8 * i)
    return f"{get_type(class_idx)}.{get_string(name_idx)}:{get_type(type_idx)}"

def get_method(i):
    class_idx, proto_idx, name_idx = struct.unpack_from('<HHI', b, method_ids_off + 8 * i)
    return f"{get_type(class_idx)}.{get_string(name_idx)}"

TARGET = None
for i in range(type_ids_size):
    if get_type(i) == CLS:
        TARGET = i
        break
if TARGET is None:
    print(f"type {CLS} not found"); sys.exit(1)
print(f"{CLS} type_idx={TARGET}")

# opcode table: (total_units, has_type_operand) — new-instance=0x22 (22c),
# check-cast=0x1f, const-class=0x1c, instance-of=0x20 (all 22c: 2 units,
# type_idx in BC at +2), new-array=0x23 (22c).
TYPE_OPCODES = {0x1c, 0x1f, 0x20, 0x22, 0x23}

# instruction size table in code units (16-bit)
def build_sizes():
    sizes = [1] * 256
    for o in list(range(0x00, 0x12)): sizes[o] = 1
    sizes[0x13] = 2; sizes[0x14] = 3; sizes[0x15] = 2          # const/16, const, const/high16
    for o in range(0x16, 0x1a): sizes[o] = 2                    # const-wide family
    sizes[0x19] = 2
    sizes[0x1a] = 2; sizes[0x1b] = 3                            # const-string(/jumbo)
    for o in range(0x1c, 0x24): sizes[o] = 2                    # const-class..new-array (22c/21c)
    sizes[0x24] = 3; sizes[0x25] = 3                            # filled-new-array(/range)
    sizes[0x26] = 3                                             # fill-array-data
    sizes[0x27] = 1                                             # throw
    sizes[0x28] = 1; sizes[0x29] = 2; sizes[0x2a] = 3           # goto family
    sizes[0x2b] = 3; sizes[0x2c] = 3                            # switches
    for o in range(0x2d, 0x32): sizes[o] = 2                    # cmp
    for o in range(0x32, 0x3e): sizes[o] = 2                    # if-eq..if-le
    for o in range(0x3e, 0x44): sizes[o] = 2                    # goto-less ifz family... (3e-43 unused)
    for o in range(0x44, 0x52): sizes[o] = 2                    # aget/aput
    for o in range(0x52, 0x60): sizes[o] = 2                    # iget/iput
    for o in range(0x60, 0x6e): sizes[o] = 2                    # sget/sput
    for o in range(0x6e, 0x73): sizes[o] = 3                    # invoke-kind
    sizes[0x74] = 3; sizes[0x75] = 3; sizes[0x76] = 3; sizes[0x77] = 3
    sizes[0x78] = 3
    for o in range(0x79, 0x7a): sizes[o] = 1
    for o in range(0x7b, 0x90): sizes[o] = 1                    # unop
    for o in range(0x90, 0xb0): sizes[o] = 2                    # binop
    for o in range(0xb0, 0xd0): sizes[o] = 1                    # binop/2addr
    for o in range(0xd0, 0xe0): sizes[o] = 2                    # binop/lit16
    for o in range(0xe0, 0xf0): sizes[o] = 2                    # binop/lit8
    sizes[0xf0] = 3  # invoke-polymorphic
    sizes[0xf1] = 3
    sizes[0xf2] = 2  # invoke-custom
    sizes[0xf3] = 2
    sizes[0xf4] = 3  # const-method-handle
    sizes[0xf5] = 3
    sizes[0xf6] = 2
    sizes[0xf7] = 2
    sizes[0xf8] = 3
    sizes[0xf9] = 3
    sizes[0xfa] = 2
    sizes[0xfb] = 2
    return sizes

SIZES = build_sizes()

def scan_method(cls, mname, code_off):
    regs, ins, outs, tries, debug_off = struct.unpack_from('<HHHHI', b, code_off)
    insns_size = struct.unpack_from('<I', b, code_off + 12)[0]
    p = code_off + 16
    hits = []
    pc = 0
    while pc < insns_size:
        op = b[p] & 0xff
        # payload pseudo-instructions (opcode 0x00 + ident at +1): variable
        # length — mis-parsing them desyncs every subsequent instruction.
        units = SIZES[op]
        if op == 0x00 and p + 4 <= len(b):
            ident = struct.unpack_from('<H', b, p + 2)[0]
            # layout: 0x00, ident(16), then payload — ident lives at unit+1
            ident = struct.unpack_from('<H', b, p + 2)[0]
            u1 = struct.unpack_from('<H', b, p + 2)[0]
            # correct: unit0 = 0x00nn where nn=ident high byte; read ident as
            # the 16-bit value at p+2 (unit+1).
            ident = struct.unpack_from('<H', b, p + 2)[0]
            if ident in (0x0100, 0x0200, 0x0300):
                sz = struct.unpack_from('<H', b, p + 4)[0]
                if ident == 0x0100:
                    units = sz * 2 + 4      # packed-switch-payload
                elif ident == 0x0200:
                    units = sz * 4 + 2      # sparse-switch-payload
                else:
                    ew = sz
                    cnt = struct.unpack_from('<I', b, p + 6)[0] if p + 10 <= len(b) else 0
                    total = ew * cnt
                    units = 4 + (total + 1) // 2   # fill-array-data-payload
        if op == 0x22 and p + 4 <= len(b):  # new-instance, type_idx @ +2
            tidx = struct.unpack_from('<H', b, p + 2)[0]
            if tidx == TARGET:
                hits.append(pc)
        pc += units
        p += units * 2
    return hits

hits_out = []
for ci in range(class_defs_size):
    base = class_defs_off + 32 * ci
    cls_idx = struct.unpack_from('<I', b, base)[0]
    cls = get_type(cls_idx)
    cdo = struct.unpack_from('<I', b, base + 24)[0]
    if cdo == 0: continue
    sfields, p = uleb(cdo)
    ifields, p = uleb(p)
    dmethods, p = uleb(p)
    vmethods, p = uleb(p)
    for _ in range(sfields + ifields):
        _, p = uleb(p); _, p = uleb(p)
    def walk_methods(n, p):
        for _ in range(n):
            midx, p = uleb(p)
            acc, p = uleb(p)
            code_off, p = uleb(p)
            if code_off == 0: continue
            mname = get_method(midx)
            hs = scan_method(cls, mname, code_off)
            for h in hs:
                hits_out.append((cls, mname, h))
        return p
    p = walk_methods(dmethods, p)
    p = walk_methods(vmethods, p)

for cls, m, pc in hits_out:
    print(f"new-instance {CLS}  in {cls}.{m}  pc={pc} (0x{pc:x})")
print(f"TOTAL sites: {len(hits_out)}")
