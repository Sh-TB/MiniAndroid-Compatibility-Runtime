#!/usr/bin/env python3
"""CONT-38 — chain-decode the compose draw cascade: Lpz0;.L0 and the links
below it. Also disasm Lz6;.i (the BOARD canvas lambda) to confirm its shape
(calls Ly3;.m at pc=303) and find what interface Lz6; implements (how it is
supposed to be dispatched)."""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location("d9", "/home/z/my-project/scripts/cont9_dexdump.py")
d9 = importlib.util.module_from_spec(spec)
sys.modules["d9"] = d9
spec.loader.exec_module(d9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
z = zipfile.ZipFile(APK)
d = d9.Dex(z.read("classes.dex"))

def disasm_method(cls, mname, max_sz=800):
    off = d.find_class(cls)
    if off is None:
        print(f"{cls}: NOT FOUND"); return
    info = d.class_methods(off)
    print(f"=== {cls} === super={info['super']} ifaces={info['ifaces'][:8]}")
    for (mn, md, acc, sz, code) in info['direct'] + info['virtual']:
        if mn == mname and code and sz <= max_sz:
            print(f"--- {cls};.{mn}{md} size={sz} ---")
            print(d.disasm(code))
    # list all methods briefly
    print("methods:")
    for kind in ("direct","virtual"):
        for (mn, md, acc, sz, code) in info[kind]:
            print(f"  {kind} {mn}{md} size={sz}")

disasm_method("Lpz0;", "L0")
disasm_method("Lz6;", "i")
