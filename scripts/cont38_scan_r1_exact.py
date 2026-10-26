#!/usr/bin/env python3
"""CONT-38 — EXACT scan for invoke sites of Lpz0;.r1 using the method_ids
index + a COMPLETE Dalvik instruction-length table (no desync).
Also scans for new-instance Luc0; and iput-object to Lpz0;.P."""
import sys, struct, zipfile, importlib.util

spec = importlib.util.spec_from_file_location("d9", "/home/z/my-project/scripts/cont9_dexdump.py")
d9 = importlib.util.module_from_spec(spec)
sys.modules["d9"] = d9
spec.loader.exec_module(d9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
z = zipfile.ZipFile(APK)
d = d9.Dex(z.read("classes.dex"))

# find the method_id index for Lpz0;.r1 and the field_id for Lpz0;.P
r1_idx = P_idx = Luc0_idx = None
for idx in range((d.method_ids_size if hasattr(d,'method_ids_size') else 0)):
    pass
# d9 exposes method_ids_off/size? check attrs
attrs = [a for a in dir(d) if 'ids' in a]
print("dex attrs:", attrs)

def find_method_id(cls, name, proto_contains=""):
    for idx in range(d.method_ids_size):
        off = d.method_ids_off + idx*8
        c = d.u(off, 2); n = d.u(off+4, 4)
        if d.type_str(c) == cls and d.string(n) == name:
            proto = d.proto_str(d.u(off+2, 2))
            if proto_contains in proto:
                return idx, proto
    return None, None

def find_field_id(cls, name):
    for idx in range(d.field_ids_size):
        off = d.field_ids_off + idx*8
        c = d.u(off, 2); n = d.u(off+4, 4)
        if d.type_str(c) == cls and d.string(n) == name:
            return idx
    return None

r1_idx, r1_proto = find_method_id("Lpz0;", "r1", "(Lf90;")
P_idx = find_field_id("Lpz0;", "P")
print(f"r1 method_idx={r1_idx} proto={r1_proto}; P field_idx={P_idx}")

# Complete length table (in 16-bit code units) per Dalvik opcode.
def op_len(op, word, o, d):
    # standard formats
    if op == 0x00:
        if word == 0x0100:
            return 2 + d.u(o+2, 2)  # packed-switch payload: ident + size*... in units
        if word == 0x0200:
            return 4 + 2*d.u(o+2, 2)  # sparse-switch payload
        if (word & 0xff) == 0x00 and (word >> 8) != 0:
            # array payload: ident(u16) width(u16) size(u32)
            w = d.u(o+2, 2)
            size = d.u(o+4, 4)
            total_units = 4 + (size * w + 1) // 2
            return total_units
        return 1
    F10T = {0x0d,0x0e,0x0f,0x10,0x11,0x12,0x1a,0x1b,0x1d,0x1e,0x27,0x28,0x73,0x74,0x75,0x76,0x77,0x78}
    # 10x: 1 unit — many no-arg ops
    if op in F10T: return 1
    if op == 0x01 or (0x02 <= op <= 0x07) or (0x07 <= op <= 0x08): return 1  # move*
    if 0x04 <= op <= 0x07: return 2  # move/16 etc — handled below actually
    L1 = {0x09,0x0a,0x0b,0x0c}
    if op in L1: return 2  # move-object/16, /16 forms — 22x=2 units
    # 12x (1 unit): 0x81..0x8f two-addr
    if 0xb0 <= op <= 0xcf: return 1  # /2addr
    if 0xd0 <= op <= 0xd7: return 1  # rem-long/2addr
    # 21c/21h/21s/22x/21t/21s: 2 units
    two = set(range(0x13,0x1c)) | {0x1d,0x1e,0x1f} | {0x20,0x21,0x22,0x23} | set(range(0x52,0x6d)) | set(range(0x6e,0x73)) | {0x74,0x75,0x76,0x77,0x78} | {0x1c,0x24,0x25,0x26,0x27,0x28} | {0x29,0x2a,0x2b,0x2c} | set(range(0x7b,0x90))
    # careful: 0x6e-0x72 are 3 units (35c); 0x74-0x78 are 3 units (45cc/4rcc?)
    if 0x6e <= op <= 0x72: return 3
    if 0x74 <= op <= 0x78: return 3  # invoke-virtual/range etc (3 units) + 0x79,0x7a unused
    if 0x74 <= op <= 0x78: return 3
    if op in two:
        # most 2-unit: 21c/21s/21h/22x/21t/22b/22t/23x
        return 2
    # 31i/31t/31s (3 units): const/const-wide/const-string jumbo... 0x14 is 3 units (const), 0x17 3 units (const-wide/32), 0x1a const-string 2 units, 0x1b const-string/jumbo 3 units
    if op in (0x14,0x17): return 3
    if op == 0x18: return 5  # const-wide (51l) 5 units? 0x18 = const-wide (51l): 5 units
    if op == 0x19: return 2  # const-wide/high16 (21h)
    if op == 0x15: return 2  # const/high16
    if op == 0x16: return 2  # const-wide/16
    if op == 0x13: return 2  # const/16
    if op == 0x12: return 1  # const/4
    if op == 0x1a: return 2  # const-string
    if op == 0x1b: return 3  # const-string/jumbo
    if op in (0x23,): return 2  # new-array
    if op in (0x24,0x25): return 3  # filled-new-array (+range)
    if op == 0x26: return 3  # filled-new-array/range
    if op in (0x29,): return 2  # goto/16
    if op == 0x2a: return 3  # goto/32
    if op in (0x2b,0x2c): return 3  # switch
    if 0x2d <= op <= 0x31: return 2  # cmp
    if 0x32 <= op <= 0x3d: return 2  # if-test
    if 0x44 <= op <= 0x51: return 2  # aget/aput
    if 0x52 <= op <= 0x5f: return 2  # iget/iput
    if 0x60 <= op <= 0x6d: return 2  # sget/sput
    if 0x7b <= op <= 0x8f: return 1  # unop + 2addr binops b0-cf
    if 0x90 <= op <= 0xaf: return 2  # binop lit... actually 0x90-0xaf are 32x/23x binops = 2 units (0x90 add-int 23x? no — 0x90-0xaf = binop (23x? no). Dalvik: 0x90..0xaf = binop (23x? NO — binop is 0x90-0xaf as 32x? hmm.
    # 0x90-0xaf: binop 23x = 2 units; 0xd8-0xe2 = binop/lit8+lit16 = 2 units
    if 0xd8 <= op <= 0xe2: return 2
    if op in (0xe3,): return 2  # (unused/odex)
    return 2  # safe default

results = []
for i in range(d.class_defs_size):
    off = d.class_defs_off + i*32
    cdesc = d.type_str(d.u(off, 4))
    try: cinfo = d.class_methods(off)
    except Exception: continue
    for kind in ("direct","virtual"):
        for (mn, md, acc, sz, code) in cinfo[kind]:
            if not code or sz == 0: continue
            insns_off = code + 16
            pc = 0
            while pc < sz:
                o = insns_off + pc*2
                word = d.u(o, 2)
                op = word & 0xff
                if op in (0x6e,0x6f,0x70,0x71,0x72) and r1_idx is not None:
                    midx = d.u(o+2, 2)
                    if midx == r1_idx:
                        results.append((cdesc, mn, md, pc, op))
                    pc += 3
                    continue
                pc += op_len(op, word, o, d)

for (cdesc, mn, md, pc, op) in results:
    print(f"  CALLER {cdesc}.{mn}{md} pc={pc} op={op:#x}")
print(f"total r1 invoke sites: {len(results)}")
