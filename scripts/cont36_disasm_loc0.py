#!/usr/bin/env python3
"""CONT-36: verify Loc0.c is the CanvasDrawScope-style draw dispatch whose
5th arg (the draw block) is excluded from the M3-19 re-entry key."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))
for c in d.get_classes():
    if c.get_name() != "Loc0;":
        continue
    print("Loc0 super:", c.get_superclassname(), "ifaces:", c.get_interfaces())
    for m in c.get_methods():
        if m.get_name() != "c":
            continue
        print("--- Loc0.c", m.get_descriptor())
        code = m.get_code()
        if not code:
            continue
        pc = 0
        for ins in m.get_instructions():
            nm = ins.get_name()
            out = ins.get_output()
            if "invoke" in nm or nm.startswith("return"):
                print(f"  pc={pc} {nm} {out[:120]}")
            pc += ins.get_length()
        break
    break
