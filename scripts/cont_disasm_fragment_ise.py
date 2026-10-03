#!/usr/bin/env python3
"""CONT-ROOT-C: disassemble androidx FragmentStateManager-ish check in the
spacevertex APK — Landroidx/fragment/app/a;.b around pc=232 (the ISE throw
site "must be a public static class"). Answers WHICH Class metadata call the
runtime answered wrongly (isMemberClass? getModifiers? both)."""
import sys, zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/run/diff366/hidden_sources/fr.arnaudguyon.spacevertex_29.apk"
TARGET = "Landroidx/fragment/app/a;"
WANT = {"b"}
SHOW = range(150, 260)

zf = zipfile.ZipFile(APK)
for name in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
    d = DEX(zf.read(name))
    for c in d.get_classes():
        if c.get_name() != TARGET:
            continue
        for m in c.get_methods():
            if m.get_name() not in WANT:
                continue
            code = m.get_code()
            if not code:
                continue
            print(f"=== {TARGET}.{m.get_name()} {m.get_descriptor()} in {name} regs={code.get_registers_size()} ===")
            pc = 0
            for ins in m.get_instructions():
                if pc in SHOW:
                    print(f"pc={pc} {ins.get_name()} {ins.get_output()}")
                pc += ins.get_length()
            sys.exit(0)
print("not found")
