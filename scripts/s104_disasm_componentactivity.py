#!/usr/bin/env python3
"""S104: disassemble ComponentActivity.<init> around pc=224 (solitaire first divergence)."""
import sys, zipfile
from loguru import logger
logger.remove()

from androguard.core.dex import DEX

APK = "/home/z/my-project/run/s99/apks/com.vayunmathur.games.solitaire.apk"
TARGET = "Landroidx/activity/ComponentActivity;"
WANT = {"<init>"}

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
                if 180 <= pc <= 260:
                    print(f"pc={pc} {ins.get_name()} {ins.get_output()}")
                pc += ins.get_length()
            sys.exit(0)
print("not found")
