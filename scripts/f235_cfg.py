#!/usr/bin/env python3
"""f235_cfg.py — full disassembly + reverse CFG for one method.
Finds every branch whose target == the pc holding a given string throw.
Usage: f235_cfg.py <apk> <Lcls;> <method> <needle-string>
"""
import sys, struct, zipfile
sys.path.insert(0, '/home/z/my-project/scripts')
from dalvik_walker import Dex, W

APK, CLS, MTH, NEEDLE = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

z = zipfile.ZipFile(APK)
d = z.read([n for n in z.namelist() if n.endswith('.dex')][0])
dx = Dex(d)
(ssz, sof) = (dx.str_ids_size, dx.str_ids_off)
(fsz, fof) = (dx.field_ids_size, dx.field_ids_off)
(msz, mof) = (dx.method_ids_size, dx.method_ids_off)

def st(i): return dx.str_at(i)
def fld(i):
    c, t, n = struct.unpack_from('<HHI', d, fof + i*8)
    return f"{dx.type_at(c)}.{st(n)}"
def mth(i):
    c, p, n = struct.unpack_from('<HHI', d, mof + i*8)
    return f"{dx.type_at(c)}.{st(n)}"

off = dx.find_class(CLS)
methods = dx.class_methods(off)
co = None
for kind, cn, mn, c in methods:
    if mn == MTH:
        co = c; break
units = dx.code_units(co)

def w2s(v):  # signed 16-bit
    return v - 0x10000 if v >= 0x8000 else v
def b2s(v):
    return v - 0x100 if v >= 0x80 else v

insns = []  # (pc, op, size, note)
pc = 0
while pc < len(units):
    w = units[pc]; op = w & 0xff; sz = W[op]
    note = ""
    if op == 0x1a:
        note = st(units[pc+1])
    elif op == 0x1b:
        note = st(units[pc+1] | (units[pc+2] << 16))
    elif op == 0x22:
        note = dx.type_at(units[pc+1])
    elif 0x52 <= op <= 0x6d:
        note = fld(units[pc+1])
    elif 0x6e <= op <= 0x72 or 0x74 <= op <= 0x78:
        note = mth(units[pc+1])
    insns.append((pc, op, sz, note))
    pc += sz

starts = set(p for p, _, _, _ in insns)
throw_pcs = [p for p, op, _, note in insns if op == 0x1a and NEEDLE in note]
print("throw const-string pcs:", [hex(p) for p in throw_pcs])

# branch map: target -> list of (pc, op, offset)
rev = {}
for p, op, sz, note in insns:
    if op in (0x28,):  # goto 10t
        t = p + b2s(units[p] >> 8)
        rev.setdefault(t, []).append((p, op, b2s(units[p] >> 8)))
    elif op in (0x29,):
        t = p + w2s(units[p+1]); rev.setdefault(t, []).append((p, op, w2s(units[p+1])))
    elif op in (0x2a,):
        t = p + (units[p+1] | units[p+2] << 16) - (1 << 32 if False else 0)
        t = p + w2s(units[p+1]) if False else (p + (units[p+1] | (units[p+2] << 16)))
        if t >= 1 << 31: t -= 1 << 32
        rev.setdefault(t, []).append((p, op, t - p))
    elif 0x32 <= op <= 0x37:  # if-cmp 22t
        t = p + b2s(units[p] >> 8); rev.setdefault(t, []).append((p, op, b2s(units[p] >> 8)))
    elif 0x38 <= op <= 0x3d:  # if-z 21t
        t = p + b2s(units[p] >> 8); rev.setdefault(t, []).append((p, op, b2s(units[p] >> 8)))

for tp in throw_pcs:
    # the throw of a const-string is followed by invoke Lg0;.a
    print(f"\n== source of throw at {tp:#06x} ({NEEDLE}) ==")
    for src, op, offv in rev.get(tp, []):
        # what's the guard just before src?
        prev = [x for x in insns if x[0] < src]
        prev3 = prev[-3:] if prev else []
        chain = " | ".join(f"{p:#x} op=0x{op:02x} {note}" for p, op, _, note in prev3)
        print(f"  branch from {src:#06x} op=0x{op:02x} off={offv}  <- prev: {chain}")
