#!/usr/bin/env python3
"""CONT-37: (a) EVERY invoke site of Luv;->I (the draw-block interface) —
the rename-hidden dispatch; (b) every construction/reference site of
Lte1/Lod1; (c) who calls Lg6.e/f (the paragraph paint helpers)."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

luv_sites = []
new_sites = {k: [] for k in ("Lte1;", "Lod1;", "Lr40;")}
lg6_sites = []

for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                nm = ins.get_name()
                out = ins.get_output()
                if nm == "new-instance" and out.split("->")[0] in new_sites:
                    new_sites[out.split("->")[0]].append(
                        (m.get_class_name(), m.get_name()))
                if "invoke" not in nm or "->" not in out:
                    continue
                pre = out.split("->")[0]
                tcls = pre.split(",")[-1].strip() if "," in pre else pre.strip()
                tm = out.split("->")[1].split(":")[0].split("(")[0]
                tdesc = out.split("->")[1].split(":")[0]
                if tcls == "Luv;" and tm == "I":
                    luv_sites.append((m.get_class_name(), m.get_name(), nm,
                                      tdesc, out.strip()[:120]))
                if tcls == "Lg6;" and tm in ("d", "e", "f"):
                    lg6_sites.append((m.get_class_name(), m.get_name(), nm,
                                      tm, out.strip()[:120]))
        except Exception:
            continue

print(f"== ALL Luv;->I invoke sites: {len(luv_sites)} ==")
for x in luv_sites:
    print(" ", x)
print()
print("== construction sites ==")
for k, v in new_sites.items():
    print(f"  {k}: {len(v)} new-instance")
    for x in v[:6]:
        print("     ", x)
print()
print(f"== Lg6.d/e/f call sites: {len(lg6_sites)} ==")
for x in lg6_sites:
    print(" ", x)
