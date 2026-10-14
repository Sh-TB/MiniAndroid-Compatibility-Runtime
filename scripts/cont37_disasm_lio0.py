#!/usr/bin/env python3
"""CONT-37: Lio0 full disassembly (who calls Ltk0.d and where the painter
object flows) + Ltk0 shape + callers of Lio0 methods."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

for c in d.get_classes():
    if c.get_name() in ("Lio0;", "Ltk0;"):
        print(f"=== {c.get_name()} super={c.get_superclassname()} ifaces={list(c.get_interfaces())} ===")
        for m in sorted(c.get_methods(), key=lambda m: m.get_name()):
            code = m.get_code()
            if not code:
                continue
            print(f"--- {m.get_name()}{m.get_descriptor()} ---")
            for ins in m.get_instructions():
                print(f"  {ins.get_name():26s} {ins.get_output().strip()[:130]}")
        print()

print("== callers of Lio0.* and Ltk0.* ==")
for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                nm = ins.get_name()
                if "invoke" not in nm:
                    continue
                out = ins.get_output().strip()
                if "->" not in out:
                    continue
                pre = out.split("->")[0]
                tcls = pre.split(",")[-1].strip() if "," in pre else pre.strip()
                if tcls in ("Lio0;", "Ltk0;"):
                    print(" ", m.get_class_name(), m.get_name(), nm, out[:110])
        except Exception:
            continue
