#!/usr/bin/env python3
"""CONT-36: Lg6 method callers with the FIXED class extraction (the earlier
scan used a broken splitter and missed interface dispatch)."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

callers = {}
for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                nm = ins.get_name()
                if "invoke" not in nm:
                    continue
                out = ins.get_output()
                if "->" not in out:
                    continue
                pre = out.split("->")[0]
                tcls = pre.split(",")[-1].strip() if "," in pre else pre.strip()
                if tcls != "Lg6;":
                    continue
                tm = out.split("->")[1].split(":")[0].split("(")[0]
                flavor = "iface" if "interface" in nm else "virt"
                callers.setdefault(f"Lg6.{tm}", []).append(
                    f"[{flavor}] {m.get_class_name()}.{m.get_name()}")
        except Exception:
            continue
for k in sorted(callers):
    u = sorted(set(callers[k]))
    print(f"{k}: {len(u)} distinct call sites")
    for x in u[:8]:
        print("   ", x)
