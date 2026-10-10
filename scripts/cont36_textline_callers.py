#!/usr/bin/env python3
"""CONT-36 Phase 3h: who calls Lsh1;.draw and Lm3;.m (the minified text-line
pipeline)? And what are Lsh1/Lm3 (super, ifaces, fields)? Decides whether the
text-paint chain exists-but-unreached or is entirely absent."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk"
z = zipfile.ZipFile(APK)
d = DEX(z.read("classes.dex"))

targets = {("Lsh1;", "draw"), ("Lm3;", "m")}
callers = {}
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
                tcls = out.split("->")[0].strip()
                tm = out.split("->")[1].split(":")[0].split("(")[0]
                if (tcls, tm) in targets:
                    callers.setdefault(f"{tcls};.{tm}", []).append(
                        f"{m.get_class_name()}.{m.get_name()}")
        except Exception:
            continue

for k, v in callers.items():
    u = sorted(set(v))
    print(f"{k}: {len(u)} callers: {u[:10]}")

for c in d.get_classes():
    if c.get_name() in ("Lsh1;", "Lm3;"):
        print(f"=== {c.get_name()} super={c.get_superclassname()} "
              f"ifaces={c.get_interfaces()} ===")
        for f in c.get_fields():
            print("  field:", f.get_name(), f.get_descriptor())
