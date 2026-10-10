#!/usr/bin/env python3
"""CONT-36: drawRenderNode call sites — receiver-class-exact scan."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))
hits = {}
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
                if tm == "drawRenderNode":
                    hits.setdefault(tcls, []).append(
                        f"{m.get_class_name()}.{m.get_name()}")
        except Exception:
            continue
for tc, ms in hits.items():
    print(tc, "->", sorted(set(ms))[:10])
print("total drawRenderNode sites:", sum(len(v) for v in hits.values()))
