#!/usr/bin/env python3
"""CONT-107 / F-NEW-452 decode: where does the null Locale in c41.run come from?

F-NEW-447 face (telegram fixed-binary run): [F447-NPE] Ljava/util/Locale;.getLanguage
caller=Lorg/telegram/ui/c41;.run — the null receiver was previously routed to the
shadow silently (ROOT-059). ART throws. This scan decodes Lorg/telegram/ui/c41;.run
to identify the register feeding the invoke and its producer (field load? static?
getDefault? parameter?).
Output: run/c107/c41_scan.txt
"""
import sys
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = sys.argv[1] if len(sys.argv) > 1 else "upload/telegram_official.apk"
OUT = "run/c107/c41_scan.txt"
L = []

a = APK(APK_PATH)
dexes = [DEX(d) for d in a.get_all_dex()]

target = None
for di, d in enumerate(dexes):
    for c in d.get_classes():
        if c.get_name() == "Lorg/telegram/ui/c41;":
            L.append(f"[c41] found in dex#{di}")
            for m in c.get_methods():
                if m.get_name() == "run":
                    target = m
                    L.append(f"[c41] run {m.get_descriptor()}")
if target is None:
    L.append("[c41] class/method NOT FOUND")
else:
    code = target.get_code()
    idx = 0
    for i in code.get_bc().get_instructions():
        op = i.get_name()
        try:
            out = i.get_output()
        except Exception:
            out = "<no-output>"
        L.append(f"  {idx:4d} {op:20s} {out}")
        idx += 1

with open(OUT, "w") as fh:
    fh.write("\n".join(L) + "\n")
print(f"wrote {OUT}: {len(L)} lines")
