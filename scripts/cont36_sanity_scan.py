#!/usr/bin/env python3
"""Sanity check the decoder: scan ONE dex, count methods with code, and find
any invoke referencing StaticLayout or drawText (loose match)."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk"
z = zipfile.ZipFile(APK)
names = [n for n in z.namelist() if n.endswith(".dex")]
print("dex files:", names)
d = DEX(z.read(names[0]))
methods = list(d.get_methods())
print("methods in dex0:", len(methods))
withcode = 0
loose = []
for m in methods:
    try:
        if m.get_code() is None:
            continue
        withcode += 1
        for ins in m.get_instructions():
            nm = ins.get_name()
            if "invoke" in nm:
                out = ins.get_output()
                if "StaticLayout" in out or "drawText" in out:
                    loose.append((m.get_class_name(), m.get_name(), nm, out.strip()[:100]))
    except Exception as e:
        continue
print("methods with code:", withcode)
print("loose matches:", len(loose))
for l in loose[:20]:
    print(l)
