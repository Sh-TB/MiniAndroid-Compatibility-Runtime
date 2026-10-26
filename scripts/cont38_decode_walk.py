#!/usr/bin/env python3
"""CONT-38 — decode the dooz re-entry walk chain classes:
Lf90; (the block interface), Lkc0; (state holder), Lho1;.u/.c, Li7;, Lto1;,
Lso1;, Lww; — with accurate lengths for the ops we care about."""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location("d9", "/home/z/my-project/scripts/cont9_dexdump.py")
d9 = importlib.util.module_from_spec(spec)
sys.modules["d9"] = d9
spec.loader.exec_module(d9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
z = zipfile.ZipFile(APK)
d = d9.Dex(z.read("classes.dex"))

def dump_class(desc, methods=None, max_methods=30):
    off = d.find_class(desc)
    if off is None:
        print(f"{desc}: NOT FOUND"); return
    info = d.class_methods(off)
    print(f"\n=== {desc} === super={info['super']} ifaces={info['ifaces']}")
    for f in info['fields'][:12]:
        print("  field", f)
    shown = 0
    for kind in ("direct", "virtual"):
        for (mname, mdesc, acc, sz, code) in info[kind]:
            if methods and mname not in methods: continue
            if shown >= max_methods: break
            print(f"  {kind} {mname}{mdesc} acc={acc:#x} size={sz} code={'Y' if code else 'N'}")
            shown += 1
    return info

# 1) Lf90; — the block interface: full method list
info = dump_class("Lf90;")
if info:
    for kind in ("direct","virtual"):
        for (mname, mdesc, acc, sz, code) in info[kind]:
            print(f"  ALL {kind} {mname}{mdesc} size={sz}")

# 2) the walk chain classes' key methods
dump_class("Lkc0;", methods={"m","<init>"})
dump_class("Lho1;", methods={"u","c","d"})
dump_class("Li7;", methods={"h"})
dump_class("Lto1;", methods={"c"})
dump_class("Lso1;", methods={"a"})
dump_class("Lww;", methods={"h","i"})

# 3) disasm the small ones
for desc, mname in [("Lho1;","c"),("Lho1;","u"),("Lho1;","d"),("Lkc0;","m"),("Li7;","h"),("Lto1;","c"),("Lso1;","a"),("Lww;","h"),("Lww;","i")]:
    off = d.find_class(desc)
    if off is None: continue
    info = d.class_methods(off)
    for (mn, md, acc, sz, code) in info['direct'] + info['virtual']:
        if mn == mname and code and sz <= 520:
            print(f"\n--- disasm {desc};.{mn}{md} size={sz} ---")
            print(d.disasm(code))
