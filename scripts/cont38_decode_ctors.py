#!/usr/bin/env python3
"""CONT-38 — decode the LayoutNode ctor chain: Lel0;.<init> and
Lpz0;.<init> — where is P (the InnerNodeCoordinator) supposed to be created
and stored? Also count every new-instance of Luc0; across the APK."""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location("d9", "/home/z/my-project/scripts/cont9_dexdump.py")
d9 = importlib.util.module_from_spec(spec)
sys.modules["d9"] = d9
spec.loader.exec_module(d9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
z = zipfile.ZipFile(APK)
d = d9.Dex(z.read("classes.dex"))

for cls in ("Lel0;", "Lpz0;", "Luc0;"):
    off = d.find_class(cls)
    if off is None: continue
    info = d.class_methods(off)
    for (mn, md, acc, sz, code) in info['direct'] + info['virtual']:
        if mn == "<init>" and code and sz <= 200:
            print(f"\n--- disasm {cls};.<init>{md} size={sz} ---")
            print(d.disasm(code))

# scan every method for new-instance Luc0; / iput-object into P
print("\n=== new-instance Luc0; sites ===")
NI = 0x22
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
                if op == NI:
                    tidx = d.u(o+2, 2)
                    try: tdesc = d.type_str(tidx)
                    except Exception: tdesc = "?"
                    if tdesc == "Luc0;":
                        print(f"  {cdesc}.{mn}{md} pc={pc}")
                if op == 0x00: pc += 1
                else:
                    if op in (0x22,0x1c,0x1f,0x20,0x23,0x24,0x25,0x1a) or 0x52 <= op <= 0x6d: pc += 2
                    elif op in (0x13,0x16,0x19,0x29,0x2a,0x2b,0x2c,0x17): pc += 2
                    elif op in (0x18,0x14): pc += 3
                    else: pc += 1
