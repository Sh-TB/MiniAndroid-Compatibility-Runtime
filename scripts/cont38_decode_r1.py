#!/usr/bin/env python3
"""CONT-38 — decode Lpz0;.r1(Lf90;,Z)V (the draw-block installer — the ONLY
site that news Luc0;) and find every invoke site of r1 across the APK."""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location("d9", "/home/z/my-project/scripts/cont9_dexdump.py")
d9 = importlib.util.module_from_spec(spec)
sys.modules["d9"] = d9
spec.loader.exec_module(d9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
z = zipfile.ZipFile(APK)
d = d9.Dex(z.read("classes.dex"))

off = d.find_class("Lpz0;")
info = d.class_methods(off)
for (mn, md, acc, sz, code) in info['direct'] + info['virtual']:
    if mn == "r1" and code:
        print(f"--- disasm Lpz0;.r1{md} size={sz} ---")
        print(d.disasm(code))

print("\n=== invoke sites of Lpz0;.r1 ===")
INVOKE_OPS = {0x6e,0x6f,0x70,0x71,0x72}
for i in range(d.class_defs_size):
    off2 = d.class_defs_off + i*32
    cdesc = d.type_str(d.u(off2, 4))
    try: cinfo = d.class_methods(off2)
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
                if op in INVOKE_OPS:
                    midx = d.u(o+2, 2)
                    try: cref, mref, mdsc = d.method_ref(midx)
                    except Exception: pc += 3; continue
                    if mref == 'r1' and cref == 'Lpz0;':
                        print(f"  {cdesc}.{mn}{md} pc={pc} op={op:#x}")
                    pc += 3
                elif op == 0x00: pc += 1
                else:
                    if op in (0x22,0x1c,0x1f,0x20,0x23,0x24,0x25,0x1a) or 0x52 <= op <= 0x6d: pc += 2
                    elif op in (0x13,0x16,0x19,0x29,0x2a,0x2b,0x2c,0x17): pc += 2
                    elif op in (0x18,0x14): pc += 3
                    else: pc += 1
