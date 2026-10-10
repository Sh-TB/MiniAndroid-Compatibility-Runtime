#!/usr/bin/env python3
"""CONT-37 fix: proper new-instance/const-class scan for Lte1/Lod1/Lr40/Lg6 +
ALL Loc0.c (CanvasDrawScope.draw) call sites — the block argument decides
who paints."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

NEW_T = {"Lte1;", "Lod1;", "Lr40;", "Lg6;", "Loc0;"}
new_sites = {k: [] for k in NEW_T}
loc0c_sites = []

for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                nm = ins.get_name()
                out = ins.get_output().strip()
                if nm == "new-instance":
                    # format: "vN, Lcls;" (no ->)
                    parts = out.split(", ")
                    if len(parts) == 2 and parts[1] in NEW_T:
                        new_sites[parts[1]].append((m.get_class_name(), m.get_name()))
                if "invoke" not in nm or "->" not in out:
                    continue
                pre = out.split("->")[0]
                tcls = pre.split(",")[-1].strip() if "," in pre else pre.strip()
                tm = out.split("->")[1].split(":")[0].split("(")[0]
                if tcls == "Loc0;" and tm == "c":
                    loc0c_sites.append((m.get_class_name(), m.get_name(), nm, out[:130]))
        except Exception:
            continue

print("== new-instance sites ==")
for k, v in new_sites.items():
    print(f"  {k}: {len(v)}")
    for x in v[:8]:
        print("     ", x)
print()
print(f"== Loc0.c call sites: {len(loc0c_sites)} ==")
for x in loc0c_sites:
    print(" ", x)
