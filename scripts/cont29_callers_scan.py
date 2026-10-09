#!/usr/bin/env python3
"""cont29_callers_scan.py — find call sites of a method across the APK DEX.
usage: cont29_callers_scan.py <apk> <method-name-substr> [class-substr]
"""
import sys, io, zipfile
from androguard.core.dex import DEX

apk, target = sys.argv[1], sys.argv[2]
sub = sys.argv[3] if len(sys.argv) > 3 else ""
raw = open(apk, "rb").read()
zf = zipfile.ZipFile(io.BytesIO(raw))
dexes = [DEX(zf.read(n)) for n in zf.namelist() if n.endswith(".dex")]
for d in dexes:
    for c in d.get_classes():
        cname = c.get_name()
        if sub and sub not in cname:
            continue
        for m in c.get_methods():
            code = m.get_code()
            if not code:
                continue
            for k, ins in enumerate(code.get_bc().get_instructions()):
                out = ins.get_output()
                if ins.get_name().startswith("invoke") and target in out:
                    print(f"{cname}.{m.get_name()}\n    @{k:#06x} {ins.get_name()} {out}")
