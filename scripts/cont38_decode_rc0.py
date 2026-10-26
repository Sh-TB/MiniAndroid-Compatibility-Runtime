#!/usr/bin/env python3
"""CONT-38 — decode Lrc0;.e(Low;,Lnk0;,J,Lf90;)V — the DrawScope dispatch
that takes the draw block (ran x203 in the C013 windows). Where does the
block go, and what gates its invocation?"""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location("d9", "/home/z/my-project/scripts/cont9_dexdump.py")
d9 = importlib.util.module_from_spec(spec)
sys.modules["d9"] = d9
spec.loader.exec_module(d9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
z = zipfile.ZipFile(APK)
d = d9.Dex(z.read("classes.dex"))

off = d.find_class("Lrc0;")
info = d.class_methods(off)
print("=== Lrc0; === super:", info['super'], "ifaces:", info['ifaces'][:8])
for f in info['fields'][:14]:
    print("  field", f)
print("methods:")
for kind in ("direct","virtual"):
    for (mn, md, acc, sz, code) in info[kind]:
        mark = " <== e" if mn == "e" else ""
        print(f"  {kind} {mn}{md} size={sz}{mark}")

for (mn, md, acc, sz, code) in info['direct'] + info['virtual']:
    if mn in ("e","c") and code and sz <= 500:
        print(f"\n--- disasm Lrc0;.{mn}{md} size={sz} ---")
        print(d.disasm(code))
