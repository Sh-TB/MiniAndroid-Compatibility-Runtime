#!/usr/bin/env python3
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
            if m.get_code() is None: continue
            for ins in m.get_instructions():
                nm = ins.get_name()
                if "invoke" not in nm: continue
                out = ins.get_output()
                if "->" not in out: continue
                pre = out.split("->")[0]
                tcls = pre.split(",")[-1].strip() if "," in pre else pre.strip()
                tm = out.split("->")[1].split(":")[0].split("(")[0]
                if (tcls, tm) in targets:
                    print(f"CALLER {m.get_class_name()}.{m.get_name()} -> {tcls}.{tm} [{nm}]")
        except Exception: continue
