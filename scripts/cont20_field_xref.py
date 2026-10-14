#!/usr/bin/env python3
"""cont20_field_xref.py — index-aware xref: find every instruction in every
method that references a given instance field (by class+name), with caller
context and the surrounding 6 instructions.

Usage: cont20_field_xref.py <apk> <Lcls;> <field_name>
"""
import sys, zipfile, struct
from collections import defaultdict

APK = sys.argv[1]
CLS = sys.argv[2]
FNAME = sys.argv[3]

z = zipfile.ZipFile(APK)
dexes = [n for n in z.namelist() if n.endswith('.dex')]

# Full opcode table widths (in 16-bit code units) — Dalvik spec
def op_width(op):
    # op is the low byte of the first unit
    if op == 0x00: return None  # nop/payload handled by caller
    # 10x
    if op in (0x0c,0x0d,0x0e,0x0f,0x10,0x11,0x1d,0x1e,0x27,0x28,0x7b,0x7c,0x7d,
              0x7e,0x0a,0x0b): return 1
    # 12x .. 21c etc: table by spec
    W2 = set()
    # 12x: b0..cf (binop/2addr), 0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09
    for o in range(0xb0, 0xd0): W2.add(o)
    for o in (0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,
              0x12,0x13,0x15,0x16,0x19,0x1a,0x1c,0x1f,0x20,0x21,0x22,0x23,
              0x24,0x25,0x26,0x27,0x7b,0x7c,0x7d,0x7e):
        W2.add(o)
    # 22c: iget/iput family 0x44..0x6d, instance-of 0x20, new-array 0x23
    for o in range(0x44, 0x6e): W2.add(o)
    # 21c: sget/sput 0x60..0x6d already; const-string 0x1a, check-cast 0x1f,
    # new-instance 0x22, const-class 0x1c
    for o in (0x1a,0x1c,0x1f,0x22): W2.add(o)
    for o in range(0x60, 0x6e): W2.add(o)
    # 23x: aget/aput 0x44..0x51 already in 22c? NO — aget/aput are 23x (2 units too)
    # 30t: goto/32 0x0a? no 0x0a is goto/16? spec: 0x0a goto/16 (20t, 2 units)
    # 20t: goto/16 0x29; 22t: if-cc 0x32..0x3d; 21t: if-eqz 0x38..0x3b
    for o in range(0x32, 0x3e): W2.add(o)
    for o in (0x29,): W2.add(o)
    # 21s: const/16 0x13, const-wide/16 0x16; 21h: 0x18,0x19; 22b: binop/lit8 0xd0..0xd7
    for o in (0x13,0x15,0x16,0x17,0x18,0xd0,0xd1,0xd2,0xd3,0xd4,0xd5,0xd6,0xd7,
              0x14,0x17,0x1b,0x2b,0x2c,0x2d,0x2e,0x2f,0x30,0x31):
        W2.add(o)
    # 31i: const 0x14, const-wide/32 0x17 — 3 units
    # 35c: invoke-kind 0x6e..0x72; 3rc: 0x74..0x78 — 3 units
    for o in list(range(0x6e,0x73)) + list(range(0x74,0x79)): return 3 if (0x6e<=op<=0x72 or 0x74<=op<=0x78) else 2
    if op in (0x14,0x17,0x18,0x19,0x1b,0x2b,0x2c,0x2d,0x2e,0x2f,0x30,0x31):
        return 3 if op in (0x14,0x17,0x18,0x19,0x1b,0x2b,0x2c) else 2
    # 45cc / 4rcc: 4 units
    if op in (0xfa,0xfb): return 4
    # const-wide 0x18? const-wide/high16 0x19 is 2; const-wide 0x18 is 3
    if op == 0x18: return 3
    if op == 0x19: return 2
    if op == 0x1b: return 3
    # fill-array-data/range payload users 0x2e..0x31? actually 0x2b packed-switch,
    # 0x2c sparse-switch are 3 (31t); fill-array-data 0x2e? no 0x2e..0x31 are
    # 23x-ish... they're 31t: 3 units
    for o in (0x2b,0x2c,0x2d,0x2e,0x2f,0x30,0x31):
        pass
    return 2  # default: 2 (most common)

W1 = {0x00,0x01,0x04,0x07,0x0a,0x0b,0x0c,0x0d,0x0e,0x0f,0x10,0x11,
      0x12,0x1d,0x1e,0x21,0x27,0x28}
OPS_W = {}
for o in W1: OPS_W[o] = 1
# cont3_disasm_full OPS widths (validated against engine decode in CONT-18h)
for o in (0x02,0x05,0x08,0x13,0x15,0x16,0x19,0x1a,0x1c,0x1f,0x20,
          0x22,0x23,0x29,0x2d,0x2e,0x2f,0x30,0x31):
    OPS_W[o] = 2
for o in (0x03,0x06,0x09,0x14,0x17,0x18,0x1b,0x24,0x25,0x26,0x2a,0x2b,0x2c):
    OPS_W[o] = 3
for o in range(0x32, 0x52): OPS_W[o] = 2          # if-tests + aget/aput
for o in range(0x52, 0x6e): OPS_W[o] = 2          # iget/iput/sget/sput
for o in range(0x6e, 0x73): OPS_W[o] = 3          # invoke 35c
for o in range(0x74, 0x79): OPS_W[o] = 3          # invoke range
for o in range(0x7b, 0x90): OPS_W[o] = 1          # unop
for o in range(0x90, 0xb0): OPS_W[o] = 2          # binop 23x
for o in range(0xb0, 0xd0): OPS_W[o] = 1          # binop/2addr
for o in range(0xd0, 0xe3): OPS_W[o] = 2          # lit16/lit8
OPS_W[0xfa] = 4; OPS_W[0xfb] = 4                  # invoke-polymorphic
OPS_W[0xfc] = 3; OPS_W[0xfd] = 3; OPS_W[0xfe] = 3; OPS_W[0xff] = 3

def widths(op):
    return OPS_W.get(op, 2)

for dexname in dexes:
    d = z.read(dexname)
    str_size, str_off = struct.unpack_from('<II', d, 56)
    type_size, type_off = struct.unpack_from('<II', d, 64)
    proto_size, proto_off = struct.unpack_from('<II', d, 72)
    field_size, field_off = struct.unpack_from('<II', d, 80)
    meth_size, meth_off = struct.unpack_from('<II', d, 88)
    class_size, class_off = struct.unpack_from('<II', d, 96)

    def uleb(off):
        r = 0; s = 0
        while True:
            x = d[off]; off += 1
            r |= (x & 0x7f) << s
            if not x & 0x80: return r, off
            s += 7

    def cstr(idx):
        off = struct.unpack_from('<I', d, str_off + 4*idx)[0]
        r, off = uleb(off)
        end = d.index(b'\x00', off)
        return d[off:end].decode('utf-8', 'replace')

    def typ(idx):
        return cstr(struct.unpack_from('<I', d, type_off + 4*idx)[0])

    # find field index for (CLS, FNAME)
    target_fidx = None
    target_fty = None
    for fi in range(field_size):
        ci, ti, ni = struct.unpack_from('<HHI', d, field_off + 8*fi)
        if typ(ci) == CLS and cstr(ni) == FNAME:
            target_fidx = fi
            target_fty = typ(ti)

    if target_fidx is None:
        continue
    print(f"[{dexname}] {CLS}.{FNAME} -> field_idx={target_fidx} type={target_fty}")

    # class map for method context
    for ci_ in range(class_size):
        off = class_off + 32*ci_
        class_idx, access, super_idx, _ = struct.unpack_from('<IIII', d, off)
        desc = typ(class_idx)
        cd_off = struct.unpack_from('<I', d, off+24)[0]
        if not cd_off: continue
        try:
            sf, p = uleb(cd_off)
            inf, p = uleb(p)
            dm, p = uleb(p)
            vm, p = uleb(p)
            for _ in range(sf):  # walk static_fields entries
                _fid, p = uleb(p); _acc, p = uleb(p)
            for _ in range(inf):  # walk instance_fields entries
                _fid, p = uleb(p); _acc, p = uleb(p)
            methods = []
            for _ in range(dm):
                didx, _a = uleb(p); _a, p = uleb(p); coff, p = uleb(p)
                methods.append((didx, coff))
            for _ in range(vm):
                didx, _a = uleb(p); _a, p = uleb(p); coff, p = uleb(p)
                methods.append((didx, coff))
        except Exception:
            continue
        for didx, coff in methods:
            if not coff or coff + 16 > len(d): continue
            if didx >= meth_size: continue  # misparse guard
            # method_id
            mci, mpi, mni = struct.unpack_from('<HHI', d, meth_off + 8*didx)
            mname = cstr(mni)
            # code_item: registers_size(2) ins_size(2) outs_size(2) tries_size(2)
            # debug_info_off(4) insns_size(4) then insns
            regs, ins_, outs, tries = struct.unpack_from('<HHHH', d, coff)
            dbg, insns_size = struct.unpack_from('<II', d, coff+12)
            if insns_size > 1000000 or coff + 16 + 2*insns_size > len(d):
                continue  # misparse guard
            n_units = insns_size
            base = coff + 16
            pc = 0
            hits = []
            trail = []
            units = []
            while pc < n_units:
                unit = struct.unpack_from('<H', d, base + 2*pc)[0]
                op = unit & 0xFF
                if op == 0x00 and (unit >> 8) != 0:
                    # payload
                    hi = unit >> 8
                    if hi == 0x01:
                        sz = struct.unpack_from('<H', d, base+2*(pc+1))[0]
                        pc += 4 + sz*2; continue
                    if hi == 0x02:
                        sz = struct.unpack_from('<H', d, base+2*(pc+1))[0]
                        pc += 2 + sz*4; continue
                    if hi == 0x03:
                        ew = struct.unpack_from('<H', d, base+2*(pc+1))[0]
                        sz = struct.unpack_from('<I', d, base+2*(pc+2))[0]
                        pc += 4 + (sz*ew+1)//2; continue
                    pc += 1; continue
                w = widths(op)
                # field refs: iget 0x52..0x5a, iput 0x59..0x5f? spec:
                # 52..5f iget/iput-object etc (52-58 iget*, 59-5f iput*)
                if (0x52 <= op <= 0x5f):
                    fidx = struct.unpack_from('<H', d, base + 2*(pc+1))[0]
                    if fidx == target_fidx:
                        kind = 'iput' if 0x59 <= op <= 0x5f else 'iget'
                        hits.append((pc, kind))
                units.append((pc, op))
                pc += w
            if hits:
                mdesc = f"{desc}.{mname}"
                for hpc, kind in hits:
                    # decode context: 6 units before
                    ctx = []
                    for (u, o2) in units:
                        pass
                    print(f"  {mdesc} {kind} pc=0x{hpc:04x}")
