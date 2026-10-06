#!/usr/bin/env python3
"""List all methods of a class with full descriptors."""
import sys, zipfile, re
sys.path.insert(0, '/home/z/my-project/tmp/w4venv/lib/python3.12/site-packages')
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
with zipfile.ZipFile(APK) as z:
    d = DEX(z.read('classes.dex'))

for c in d.get_classes():
    if c.get_name() == sys.argv[1]:
        print("super:", c.get_superclassname())
        print("interfaces:", list(c.get_interfaces()))
        for m in c.get_methods():
            cl = m.get_code() and m.get_code().get_length() or 0
            print(f"  {m.get_name()} {m.get_descriptor()}  len={cl}")
        break
