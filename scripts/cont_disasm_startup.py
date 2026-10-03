#!/usr/bin/env python3
"""CONT-ROOT-A: disassemble androidx/startup/InitializationProvider.onCreate
around pc=79 in spacevertex (where Lzc; escaped) to name the next frontier."""
import sys, zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/run/diff366/hidden_sources/fr.arnaudguyon.spacevertex_29.apk"

zf = zipfile.ZipFile(APK)
for name in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
    d = DEX(zf.read(name))
    for c in d.get_classes():
        if c.get_name() != "Landroidx/startup/InitializationProvider;":
            continue
        for m in c.get_methods():
            if m.get_name() != "onCreate":
                continue
            code = m.get_code()
            print(f"=== InitializationProvider.onCreate {m.get_descriptor()} ===")
            pc = 0
            for ins in code.get_bc().get_instructions():
                if pc <= 110:
                    print(f"pc={pc} {ins.get_name()} {ins.get_output()}")
                pc += ins.get_length()
            sys.exit(0)
print("not found")
