#!/usr/bin/env python3
"""S104: dump the APK's Lkotlin/text/MatcherMatchResult; class definition (R8 merged class?)."""
import sys, zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/run/s99/apks/com.vayunmathur.games.solitaire.apk"
TARGET = "Lkotlin/text/MatcherMatchResult;"

zf = zipfile.ZipFile(APK)
for name in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
    d = DEX(zf.read(name))
    for c in d.get_classes():
        if c.get_name() != TARGET:
            continue
        print(f"=== {TARGET} defined in {name} ===")
        print("super:", c.get_superclassname())
        ifs = c.get_interfaces()
        print("interfaces:", ifs)
        print("--- fields ---")
        for f in c.get_fields():
            print("  ", f.get_name(), f.get_descriptor())
        print("--- methods ---")
        for m in c.get_methods():
            print("  ", m.get_name(), m.get_descriptor())
        sys.exit(0)
print("class NOT DEFINED in APK (only referenced)")
