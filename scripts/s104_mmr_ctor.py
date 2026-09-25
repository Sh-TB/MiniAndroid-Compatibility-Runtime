#!/usr/bin/env python3
"""S104: disassemble the R8-merged MatcherMatchResult constructors (classId switch dispatch)."""
import sys, zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/run/s99/apks/com.vayunmathur.games.solitaire.apk"
TARGET = "Lkotlin/text/MatcherMatchResult;"
WANTS = ["(Landroidx/savedstate/internal/SavedStateRegistryImpl; B)V",
         "(Ljava/lang/Object; Ljava/lang/Object; B)V"]

zf = zipfile.ZipFile(APK)
for name in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
    d = DEX(zf.read(name))
    for c in d.get_classes():
        if c.get_name() != TARGET:
            continue
        for m in c.get_methods():
            if m.get_name() != "<init>":
                continue
            desc = m.get_descriptor()
            if desc not in WANTS:
                continue
            print(f"=== <init>{desc} ===")
            pc = 0
            for ins in m.get_instructions():
                op = ins.get_name()
                out = ins.get_output()
                print(f"pc={pc} {op} {out}")
                pc += ins.get_length()
