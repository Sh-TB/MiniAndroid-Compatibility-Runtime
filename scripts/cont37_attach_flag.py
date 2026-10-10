#!/usr/bin/env python3
"""CONT-37: Lok0.u0 / Lok0.v0 (attach/detach — the r-flag writers) +
their call sites."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

for c in d.get_classes():
    if c.get_name() == "Lok0;":
        print(f"=== Lok0 super={c.get_superclassname()} ifaces={list(c.get_interfaces())} ===")
        for m in c.get_methods():
            if m.get_name() in ("u0", "v0"):
                print(f"--- {m.get_name()}{m.get_descriptor()} ---")
                for ins in m.get_instructions():
                    print(f"  {ins.get_name():24s} {ins.get_output().strip()[:120]}")
                print()

print("== callers of u0()/v0() (any class) ==")
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
                tm = out.split("->")[1].split(":")[0].split("(")[0]
                if tcls == "Lok0;" and tm in ("u0", "v0"):
                    print(" ", m.get_class_name(), m.get_name(), nm, tm, out[:100])
        except Exception:
            continue
