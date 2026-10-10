#!/usr/bin/env python3
"""CONT-37: disassemble the text-painter flow hubs:
Lqe1.d (constructs Lte1), Lld1.d (constructs Lod1), Lmo0.D0 and Loc0.a
(the two Loc0.c dispatch sites)."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

WANT = {("Lqe1;", "d"), ("Lld1;", "d"), ("Lmo0;", "D0"), ("Loc0;", "a")}

for c in d.get_classes():
    for m in c.get_methods():
        if (c.get_name(), m.get_name()) not in WANT:
            continue
        code = m.get_code()
        if not code:
            continue
        print(f"=== {c.get_name()}.{m.get_name()}{m.get_descriptor()} ===")
        for ins in m.get_instructions():
            print(f"  {ins.get_name():26s} {ins.get_output().strip()[:130]}")
        print()
