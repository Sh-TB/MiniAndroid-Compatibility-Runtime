#!/usr/bin/env python3
"""CONT-37: full disassembly of Lte1.I and Lod1.I — where does the body
divert before the Lg6.e/f paragraph-paint calls?"""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

WANT = {("Lte1;", "I"), ("Lod1;", "I")}

for c in d.get_classes():
    for m in c.get_methods():
        if (c.get_name(), m.get_name()) in WANT and m.get_descriptor() == "(Loc0;)V":
            print(f"=== {c.get_name()}.{m.get_name()}{m.get_descriptor()} ===")
            for i, ins in enumerate(m.get_instructions()):
                print(f"  {i:3d} {ins.get_name():24s} {ins.get_output().strip()[:130]}")
            print()
