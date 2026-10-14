#!/usr/bin/env python3
"""CONT-36: the text-paint chain upward — callers of Lod1.I / Lte1.I (the
Lg6 paint entry points); do those callers appear at runtime?"""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

targets = {("Lod1;", "I"), ("Lte1;", "I")}
for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                if "invoke" not in ins.get_name():
                    continue
                out = ins.get_output()
                if "->" not in out:
                    continue
                pre = out.split("->")[0]
                tcls = pre.split(",")[-1].strip() if "," in pre else pre.strip()
                tm = out.split("->")[1].split(":")[0].split("(")[0]
                if (tcls, tm) in targets:
                    print(f"CALLER {m.get_class_name()}.{m.get_name()} -> "
                          f"{tcls}.{tm} | {out.strip()[:90]}")
        except Exception:
            continue
