#!/usr/bin/env python3
"""CONT-36: callers of Lxk0.m and Lm3.l (the other drawRenderNode helpers)
+ their bodies + whether Lxk0.m-shape runs at runtime."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

targets = {("Lxk0;", "m"), ("Lm3;", "l"), ("Ly40;", "s")}
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
                    print("CALLER:", m.get_class_name(), m.get_name(),
                          "->", tcls + "." + tm, out.strip()[:90])
        except Exception:
            continue

print()
for c in d.get_classes():
    if c.get_name() not in ("Lxk0;", "Lm3;"):
        continue
    for m in c.get_methods():
        if (c.get_name(), m.get_name()) not in targets:
            continue
        code = m.get_code()
        if not code:
            continue
        print(f"--- {c.get_name()}.{m.get_name()} {m.get_descriptor()} ---")
        pc = 0
        for ins in m.get_instructions():
            nm = ins.get_name()
            out = ins.get_output()
            if "invoke" in nm or nm.startswith("return"):
                print(f"  pc={pc} {nm} {out[:110]}")
            pc += ins.get_length()
