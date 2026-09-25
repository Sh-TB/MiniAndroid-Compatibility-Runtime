#!/usr/bin/env python3
"""S104: full ComponentActivity.<init> trace — find what produces the null receiver (v1) at pc=448."""
import sys, zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/run/s99/apks/com.vayunmathur.games.solitaire.apk"
TARGET = "Landroidx/activity/ComponentActivity;"

zf = zipfile.ZipFile(APK)
for name in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
    d = DEX(zf.read(name))
    for c in d.get_classes():
        if c.get_name() != TARGET:
            continue
        for m in c.get_methods():
            if m.get_name() != "<init>" or m.get_descriptor() != "()V":
                continue
            pc = 0
            for ins in m.get_instructions():
                op = ins.get_name()
                out = ins.get_output()
                if (pc >= 260 and pc <= 470) or op.startswith("invoke") or op.startswith(("iput", "iget")):
                    print(f"pc={pc} {op} {out}")
                pc += ins.get_length()
            sys.exit(0)
