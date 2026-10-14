#!/usr/bin/env python3
"""cont29_pkg_census.py — class census by top-2 package segments (non-androidx/kotlin/java)."""
import sys, io, zipfile, collections
from androguard.core.dex import DEX
raw = open(sys.argv[1], "rb").read()
zf = zipfile.ZipFile(io.BytesIO(raw))
c = collections.Counter()
for n in zf.namelist():
    if not n.endswith(".dex"): continue
    d = DEX(zf.read(n))
    for cl in d.get_classes():
        name = cl.get_name()[1:-1]  # strip L;
        seg = "/".join(name.split("/")[:3])
        if any(name.startswith(p) for p in ("androidx/","kotlin/","kotlinx/","java/","android/","com/google/")):
            continue
        c[seg] += 1
for k, v in c.most_common(20):
    print(f"{v:6d}  L{k}/;")
