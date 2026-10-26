#!/usr/bin/env python3
"""CONT-38 — COMPLETE Dalvik instruction-length table (no desync) — exact
scan for new-instance Lz6; / invoke Lz6;.<init> / invoke Lpz0;.r1."""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location("d9", "/home/z/my-project/scripts/cont9_dexdump.py")
d9 = importlib.util.module_from_spec(spec)
sys.modules["d9"] = d9
spec.loader.exec_module(d9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
z = zipfile.ZipFile(APK)
d = d9.Dex(z.read("classes.dex"))

def find_type_id(desc):
    for idx in range(d.type_ids_size):
        if d.type_str(d.u(d.type_ids_off + idx*4, 4)) == desc:
            return idx
    return None

def find_method_id(cls, name):
    for idx in range(d.method_ids_size):
        off = d.method_ids_off + idx*8
        if d.type_str(d.u(off, 2)) == cls and d.string(d.u(off+4, 4)) == name:
            return idx
    return None

# COMPLETE length table, units (16-bit)
LEN = {}
LEN[0x00] = 'nop'
for o in (0x01, 0x04, 0x07, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, 0x11,
          0x12, 0x1d, 0x1e, 0x21, 0x27, 0x28, 0x73, 0x79, 0x7a):
    LEN[o] = 1
for o in (0x02, 0x05, 0x08, 0x13, 0x15, 0x16, 0x19, 0x1a, 0x1c, 0x1f, 0x20,
          0x22, 0x23, 0x29):
    LEN[o] = 2
for o in (0x03, 0x06, 0x09):
    LEN[o] = 3
for o in (0x14, 0x17, 0x1b, 0x24, 0x25, 0x26, 0x2a, 0x2b, 0x2c):
    LEN[o] = 3
LEN[0x18] = 5
for o in range(0x2d, 0x52): LEN[o] = 2   # cmp, if-test, aget/aput
for o in range(0x52, 0x6e): LEN[o] = 2   # iget/iput/sget/sput
for o in range(0x6e, 0x73): LEN[o] = 3   # invoke-*
for o in range(0x74, 0x79): LEN[o] = 3   # invoke-*-range
for o in range(0x7b, 0x90): LEN[o] = 1   # unop + 2addr
for o in range(0x90, 0xb0): LEN[o] = 2   # binop
for o in range(0xb0, 0xd0): LEN[o] = 1   # binop/2addr
for o in range(0xd0, 0xe3): LEN[o] = 2   # binop/lit

def op_len(op, word, o, d):
    if op == 0x00:
        if word == 0x0100:
            return 4 + 2 * d.u(o+2, 2)          # packed-switch payload
        if word == 0x0200:
            return 2 + 4 * d.u(o+2, 2)          # sparse-switch payload
        if (word >> 8) != 0:                     # fill-array-data payload
            w = d.u(o+2, 2); size = d.u(o+4, 4)
            return 4 + (size * w + 1) // 2
        return 1
    return LEN.get(op, 2)

z6_t = find_type_id("Lz6;")
z6_init = find_method_id("Lz6;", "<init>")
r1_idx = find_method_id("Lpz0;", "r1")
my_idx = find_method_id("Lmy;", "<init>")
print(f"Lz6; type={z6_t} init={z6_init}; Lpz0;.r1={r1_idx}; Lmy;.init={my_idx}")

def scan(target_ni=None, target_inv=None, label=""):
    hits_ni, hits_inv = [], []
    for i in range(d.class_defs_size):
        off = d.class_defs_off + i*32
        cdesc = d.type_str(d.u(off, 4))
        try: cinfo = d.class_methods(off)
        except Exception: continue
        for kind in ("direct", "virtual"):
            for (mn, md, acc, sz, code) in cinfo[kind]:
                if not code or sz == 0: continue
                insns_off = code + 16
                pc = 0
                while pc < sz:
                    o = insns_off + pc*2
                    word = d.u(o, 2); op = word & 0xff
                    if op == 0x22:
                        if target_ni is not None and d.u(o+2, 2) == target_ni:
                            hits_ni.append((cdesc, mn, md, pc))
                        pc += 2; continue
                    if 0x6e <= op <= 0x72:
                        if target_inv is not None and d.u(o+2, 2) == target_inv:
                            hits_inv.append((cdesc, mn, md, pc, op))
                        pc += 3; continue
                    pc += op_len(op, word, o, d)
    print(f"{label} new-instance: {hits_ni}")
    print(f"{label} invoke: {hits_inv}")

scan(target_ni=z6_t, target_inv=z6_init, label="Lz6;")
scan(target_inv=r1_idx, label="Lpz0;.r1")
scan(target_inv=my_idx, label="Lmy;.<init>")
