#!/usr/bin/env python3
"""S72: disassemble Lid;.M and Lid;.K from dooz APK — null-array producer hunt."""
import sys
from androguard.core.bytecodes.dvm import DalvikVMFormat as DEX

APK = "/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apk"
TARGETS = [("Lrz1;", "l")]

# Pull classes.dex straight from the zip (no full APK parse needed).
import zipfile
with zipfile.ZipFile(APK) as z:
    names = [n for n in z.namelist() if n.endswith(".dex")]
    dex_data = {}
    for n in names:
        dex_data[n] = z.read(n)

for dname, raw in dex_data.items():
    d = DEX(raw)
    for m in d.get_methods():
        cls = m.get_class_name()
        mname = m.get_name()
        if (cls, mname) in TARGETS:
            code = m.get_code()
            print(f"\n=== {cls}->{mname}{m.get_descriptor()}  ({dname}) ===")
            if code is None:
                print("  <abstract/native>")
                continue
            bc = code.get_bc()
            for idx, ins in enumerate(bc.get_instructions()):
                op = ins.get_name()
                out = ins.get_output()
                print(f"  {idx:4d}: {op:28s} {out}")
                if False:
                    print("  ... (truncated)")
                    break
