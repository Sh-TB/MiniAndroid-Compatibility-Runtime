#!/usr/bin/env python3
"""Disassemble La0/a;.<init> — robust instruction dump (get_offset varies by API)."""
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
                pc = 0
                for ins in meth.get_instructions():
                    op = ins.get_name()
                    out = ""
                    try: out = ins.get_output()
                    except Exception: pass
                    sz = ins.get_length()
                    print(f"  pc={pc:#05x} {op:<26} {out}")
                    pc += sz
os.unlink(dpath)
