#!/usr/bin/env python3
"""cont81_decode_loader.py — decode the libGDX SharedLibraryLoader/Os
<clinit> + load() decision bytecode from stack.tower3d's dex (androguard).
The engine's own decode is the authority; this is the cross-check.
"""
import sys
import zipfile

from loguru import logger
logger.remove()  # silence androguard debug spam

from androguard.core.dex import DEX

APK = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/z/my-project/upload/canonical_apks/stack.tower3d_1.apk"

z = zipfile.ZipFile(APK)
dex_bytes = z.read("classes.dex")
d = DEX(dex_bytes)

TARGETS = {"Lcom/badlogic/gdx/utils/SharedLibraryLoader;",
           "Lcom/badlogic/gdx/utils/Os;"}

for cls in d.get_classes():
    cname = cls.get_name()
    if cname not in TARGETS:
        continue
    for m in cls.get_methods():
        name = m.get_name()
        if name not in ("<clinit>", "load", "loadFile", "readFile"):
            continue
        code = m.get_code()
        if code is None:
            continue
        print(f"=== {cname}.{name} regs={code.get_registers_size()}"
              f" insns={code.get_insns_size()}")
        for ins in m.get_instructions():
            op = ins.get_name()
            out = ins.get_output()
            if op in ("const-string", "const-string/jumbo") or \
               "getProperty" in out or op.startswith("sget") or \
               op.startswith("invoke"):
                print(f"  {op:22s} {out[:90]}")
