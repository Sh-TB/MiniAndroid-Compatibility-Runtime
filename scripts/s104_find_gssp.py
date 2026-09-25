#!/usr/bin/env python3
"""S104: find every method that references getSavedStateProvider / SavedStateRegistryController in the solitaire APK."""
import sys, zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/run/s99/apks/com.vayunmathur.games.solitaire.apk"
NEEDLES = ("getSavedStateProvider", "SavedStateRegistryController", "performAttach")

zf = zipfile.ZipFile(APK)
for name in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
    d = DEX(zf.read(name))
    for c in d.get_classes():
        for m in c.get_methods():
            code = m.get_code()
            if not code:
                continue
            found = []
            pc = 0
            for ins in m.get_instructions():
                outp = ins.get_output()
                if any(n in outp for n in NEEDLES):
                    found.append(f"    pc={pc} {ins.get_name()} {outp}")
                pc += ins.get_length()
            if found:
                print(f"{c.get_name()}.{m.get_name()}{m.get_descriptor()}")
                for f in found[:8]:
                    print(f)
