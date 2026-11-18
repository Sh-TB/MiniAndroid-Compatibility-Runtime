#!/usr/bin/env python3
"""Disassemble La0/a;.<init> (Notepad autofill helper) — find the calls before the ISE."""
from androguard.misc import AnalyzeDex
import zipfile, tempfile, os
apk = "/home/z/my-project/upload/handoff_apks/com.farmerbb.notepad_122.apk"
z = zipfile.ZipFile(apk)
with tempfile.NamedTemporaryFile(suffix=".dex", delete=False) as f:
    f.write(z.read("classes.dex")); dpath = f.name
a, d, dx = AnalyzeDex(dpath)
for m in d.get_classes():
    if m.get_name() == "La0/a;":
        for meth in m.get_methods():
            if meth.get_name() == "<init>":
                print("METHOD:", meth.get_descriptor())
                for ins in meth.get_instructions():
                    print(f"  {ins.get_offset():#06x} {ins.get_name():<28} {ins.get_output()}")
os.unlink(dpath)
