#!/usr/bin/env python3
"""CONT-37: disassemble Lmo0.K0 (draw-node fetch), Lmo0.Z0 (fallback),
Lno0.f (node flag computation) — the K0(4) → Lte1.I gating logic."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

WANT = {("Lmo0;", "K0"), ("Lmo0;", "Z0"), ("Lno0;", "f")}

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
