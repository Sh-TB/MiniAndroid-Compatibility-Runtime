#!/usr/bin/env python3
"""CONT-38 — decode Luc0;.g()V (the draw coordinator entry that RUNS x205 in
the C013 draw windows but produces no block dispatch) + Lug0;.h1 + Lxk0;.h1
(the draw-modifier dispatch links that run) — find the dead branch."""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location("d9", "/home/z/my-project/scripts/cont9_dexdump.py")
d9 = importlib.util.module_from_spec(spec)
sys.modules["d9"] = d9
spec.loader.exec_module(d9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
z = zipfile.ZipFile(APK)
d = d9.Dex(z.read("classes.dex"))

def disasm(cls, mname):
    off = d.find_class(cls)
    if off is None:
        print(f"{cls}: NOT FOUND"); return
    info = d.class_methods(off)
    print(f"=== {cls} === super={info['super']} ifaces={info['ifaces'][:6]}")
    for f in info['fields'][:8]:
        print("  field", f)
    for (mn, md, acc, sz, code) in info['direct'] + info['virtual']:
        if mn == mname and code:
            print(f"--- {cls};.{mn}{md} size={sz} ---")
            print(d.disasm(code))

disasm("Luc0;", "g")
disasm("Luc0;", "f")
disasm("Lxk0;", "h1")
