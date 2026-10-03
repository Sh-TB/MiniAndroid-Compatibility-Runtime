#!/usr/bin/env python3
"""CONT-ROOT-C: full instruction dump of Landroidx/fragment/app/a;.b pc=0..100
to reconstruct the exact Class-metadata check → ISE branch."""
import sys, zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/run/diff366/hidden_sources/fr.arnaudguyon.spacevertex_29.apk"

zf = zipfile.ZipFile(APK)
for name in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
    d = DEX(zf.read(name))
    for c in d.get_classes():
        if c.get_name() != "Landroidx/fragment/app/a;":
            continue
        for m in c.get_methods():
            if m.get_name() != "b" or "Fragment;" not in m.get_descriptor():
                continue
            code = m.get_code()
            print(f"=== a.b {m.get_descriptor()} regs={code.get_registers_size()} ===")
            pc = 0
            for ins in code.get_bc().get_instructions():
                if pc <= 130:
                    print(f"pc={pc} {ins.get_name()} {ins.get_output()}")
                pc += ins.get_length()
            sys.exit(0)
print("not found")
