#!/usr/bin/env python3
"""CONT-37: full disassembly of Lg6.d / Lg6.e / Lg6.f — the paragraph
paint helpers between the painter body and Layout.draw."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

for c in d.get_classes():
    if c.get_name() == "Lg6;":
        for m in c.get_methods():
            if m.get_name() in ("d", "e", "f"):
                print(f"--- Lg6.{m.get_name()}{m.get_descriptor()} ---")
                for i, ins in enumerate(m.get_instructions()):
                    print(f"  {i:3d} {ins.get_name():24s} {ins.get_output().strip()[:130]}")
                print()
