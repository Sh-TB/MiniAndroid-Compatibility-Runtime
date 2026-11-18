#!/usr/bin/env python3
"""Disassemble La0/a;.<init> from whichever dex holds it."""
from androguard.misc import AnalyzeDex
import zipfile, tempfile, os
apk = "/home/z/my-project/upload/handoff_apks/com.farmerbb.notepad_122.apk"
z = zipfile.ZipFile(apk)
found = False
for name in ("classes.dex", "classes2.dex"):
    if name not in z.namelist(): continue
    with tempfile.NamedTemporaryFile(suffix=".dex", delete=False) as f:
        f.write(z.read(name)); dpath = f.name
    try:
        a, d, dx = AnalyzeDex(dpath)
        for m in d.get_classes():
            if m.get_name() == "La0/a;":
                found = True
                print(f"FOUND in {name}")
                for meth in m.get_methods():
                    if meth.get_name() == "<init>":
                        print("METHOD:", meth.get_descriptor())
                        for ins in meth.get_instructions():
                            print(f"  {ins.get_offset():#06x} {ins.get_name():<26} {ins.get_output()}")
    except Exception as e:
        print(name, "parse err", str(e)[:90])
    os.unlink(dpath)
    if found: break
if not found: print("La0/a not found in either dex")
