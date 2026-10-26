#!/usr/bin/env python3
"""CONT-40 — decode Lz/f;.<init> and La8/d;.<init> from the telegram APK
(the constructors that allocate the 1GB / 2.9GB giant blocks) — find the
huge allocation (new-array / reserve) inside them."""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location("d9", "/home/z/my-project/scripts/cont9_dexdump.py")
d9 = importlib.util.module_from_spec(spec)
sys.modules["d9"] = d9
spec.loader.exec_module(d9)

APK = "/home/z/my-project/upload/telegram_official.apk"
z = zipfile.ZipFile(APK)
dexnames = sorted(n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex'))
print("dexes:", dexnames)

for dexname in dexnames:
    d = d9.Dex(z.read(dexname))
    for cls in ("Lz/f;", "La8/d;"):
        off = d.find_class(cls)
        if off is None:
            continue
        info = d.class_methods(off)
        print(f"\n=== {dexname} {cls} === super={info['super']} ifaces={info['ifaces'][:5]}")
        for f in info['fields'][:8]:
            print("  field", f)
        for (mn, md, acc, sz, code) in info['direct'] + info['virtual']:
            if mn == "<init>" and code and sz < 400:
                print(f"--- {cls};.<init>{md} size={sz} ---")
                print(d.disasm(code))
