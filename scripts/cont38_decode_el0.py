#!/usr/bin/env python3
"""CONT-38 — decode Lel0;.i(Ldi;,Lrc0;)V — the compose Root/LayoutNode draw
cascade entry that Lt4;.dispatchDraw calls. Find the next links and where
the chain can die before reaching the CanvasDrawScope dispatch."""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location("d9", "/home/z/my-project/scripts/cont9_dexdump.py")
d9 = importlib.util.module_from_spec(spec)
sys.modules["d9"] = d9
spec.loader.exec_module(d9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
z = zipfile.ZipFile(APK)
d = d9.Dex(z.read("classes.dex"))

def show(desc, only=None, maxn=40):
    off = d.find_class(desc)
    if off is None:
        print(f"{desc}: NOT FOUND"); return
    info = d.class_methods(off)
    print(f"=== {desc} === super={info['super']} ifaces={info['ifaces'][:6]}")
    for f in info['fields'][:10]:
        print("  field", f)
    n=0
    for kind in ("direct","virtual"):
        for (mname, mdesc, acc, sz, code) in info[kind]:
            if only and mname not in only: continue
            if n>=maxn: break
            print(f"  {kind} {mname}{mdesc} acc={acc:#x} size={sz}")
            n+=1
    return info

info = show("Lel0;", only={"i","j","k","l","m","n","o","p","q"})
# disasm i() and nearby draw-ish methods
if info:
    for (mname, mdesc, acc, sz, code) in info['direct'] + info['virtual']:
        if mname in ("i","j","k") and code and sz < 700:
            print(f"\n--- disasm Lel0;.{mname}{mdesc} size={sz} ---")
            print(d.disasm(code))
