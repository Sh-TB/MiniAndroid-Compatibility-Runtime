#!/usr/bin/env python3
"""CONT-36: find invoke-interface sites for the layer-draw lambda shape
(Luv;->I(Loc0;)V) and dump the enclosing methods (the composite driver)."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

sites = []
for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                if "invoke-interface" not in ins.get_name():
                    continue
                out = ins.get_output()
                if "Luv;->I(Loc0;)V" in out:
                    sites.append((m.get_class_name(), m.get_name(),
                                  out.strip()[:100]))
        except Exception:
            continue
print(f"invoke-interface Luv;->I(Loc0;)V sites: {len(sites)}")
for s in sites[:15]:
    print(" ", s)
