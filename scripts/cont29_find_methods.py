#!/usr/bin/env python3
"""cont29_find_methods.py — list methods by name across DEX (no disasm).
usage: cont29_find_methods.py <apk> <name-regex> [class-regex]
"""
import sys, io, zipfile, re
from androguard.core.dex import DEX
apk, nre = sys.argv[1], re.compile(sys.argv[2])
cre = re.compile(sys.argv[3]) if len(sys.argv) > 3 else None
raw = open(apk, "rb").read()
zf = zipfile.ZipFile(io.BytesIO(raw))
for n in zf.namelist():
    if not n.endswith(".dex"): continue
    d = DEX(zf.read(n))
    for c in d.get_classes():
        if cre and not cre.search(c.get_name()): continue
        for m in c.get_methods():
            if nre.search(m.get_name()):
                print(f"{c.get_name()}.{m.get_name()} {m.get_descriptor()}")
