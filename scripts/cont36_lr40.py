#!/usr/bin/env python3
"""CONT-36: the composite chain upward — callers of Lr40.I and
Lkd1.drawRenderNode; Lr40 class shape; runtime presence check helper."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

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
                if (tcls == "Lr40;" and tm == "I") or \
                   (tcls == "Lkd1;" and tm == "drawRenderNode"):
                    print("CALLER:", m.get_class_name(), m.get_name(),
                          "->", tcls + ";" + tm, "|", out.strip()[:100])
        except Exception:
            continue

print()
for c in d.get_classes():
    if c.get_name() == "Lr40;":
        print("Lr40 super:", c.get_superclassname(), "ifaces:",
              c.get_interfaces())
        for m in c.get_methods():
            code = m.get_code()
            if not code:
                continue
            print(f"  method {m.get_name()} {m.get_descriptor()} size={code.get_insns_size()}")
