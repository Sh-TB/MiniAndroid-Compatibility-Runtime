#!/usr/bin/env python3
"""CONT-37: Lno0.e (flag bits for non-Lmr nodes) + Lno0.g (flag validity)
+ Lgc0.Z0 (the Z0 family — who falls back) + the Lmo0.C0 wrapper."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

WANT = {("Lno0;", "e"), ("Lno0;", "g"), ("Lgc0;", "Z0"), ("Lmo0;", "C0")}

for c in d.get_classes():
    for m in c.get_methods():
        if (c.get_name(), m.get_name()) in WANT:
            code = m.get_code()
            if not code:
                continue
            print(f"=== {c.get_name()}.{m.get_name()}{m.get_descriptor()} ===")
            for ins in m.get_instructions():
                print(f"  {ins.get_name():26s} {ins.get_output().strip()[:130]}")
            print()
