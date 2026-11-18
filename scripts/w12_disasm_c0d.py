#!/usr/bin/env python3
"""Disassemble LC0/d.j(Context, Class) = ContextCompat.getSystemService."""
from androguard.misc import AnalyzeDex
import zipfile, tempfile, os
apk = "/home/z/my-project/upload/handoff_apks/com.farmerbb.notepad_122.apk"
z = zipfile.ZipFile(apk)
with tempfile.NamedTemporaryFile(suffix=".dex", delete=False) as f:
    f.write(z.read("classes.dex")); dpath = f.name
a, d, dx = AnalyzeDex(dpath)
for m in d.get_classes():
    if m.get_name() == "LC0/d;":
        for meth in m.get_methods():
            if meth.get_name() == "j":
                print("LC0/d.j", meth.get_descriptor())
                pc = 0
                for ins in meth.get_instructions():
                    out = ""
                    try: out = ins.get_output()
                    except Exception: pass
                    print(f"  pc={pc:#05x} {ins.get_name():<24} {out}")
                    pc += ins.get_length()
os.unlink(dpath)
