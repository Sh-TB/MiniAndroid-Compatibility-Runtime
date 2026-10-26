#!/usr/bin/env python3
"""CONT-41 — decode the registerUriForScheme chain in the capacitor APKs.
Dumps WebViewLocalServer.registerUriForScheme + hostAssets + createHostingDetails
with byte offsets so the pc=0x1a NPE site can be named op-level."""
import sys, zipfile, tempfile, os
from androguard.misc import AnalyzeDex

apk = sys.argv[1]
WANT = ["registerUriForScheme", "hostAssets", "createHostingDetails"]
CLS = "Lcom/getcapacitor/WebViewLocalServer;"

with zipfile.ZipFile(apk) as z:
    dexes = [n for n in z.namelist() if n.endswith('.dex')]

for name in dexes:
    tmp = tempfile.NamedTemporaryFile(suffix='.dex', delete=False)
    tmp.write(zipfile.ZipFile(apk).read(name))
    tmp.close()
    try:
        _, d, _ = AnalyzeDex(tmp.name)
    except Exception:
        os.unlink(tmp.name)
        continue
    for c in d.get_classes():
        if c.get_name() != CLS:
            continue
        for m in c.get_methods():
            if m.get_name() not in WANT:
                continue
            print(f"\n== {CLS}.{m.get_name()}{m.get_descriptor()} [{name}] ==")
            code = m.get_code()
            if code is None:
                print("  (no code)")
                continue
            off = 0
            for ins in m.get_instructions():
                print(f"0x{off:04x}: {ins.get_name()} {ins.get_output()}")
                off += ins.get_length()
    os.unlink(tmp.name)
