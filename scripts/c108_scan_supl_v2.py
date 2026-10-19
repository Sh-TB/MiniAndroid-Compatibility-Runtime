#!/usr/bin/env python3
"""CONT-108: robust disassembly of SlidingUpPanelLayout.onMeasure using str(ins).
Output: run/c108/oc_supl_onmeasure_v2.txt
"""
import sys, logging
logging.getLogger("androguard").setLevel(logging.ERROR)
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = sys.argv[1] if len(sys.argv) > 1 else "upload/opencalculator_53.apk"
OUT = "run/c108/oc_supl_onmeasure_v2.txt"
L = []

a = APK(APK_PATH)
dexes = [DEX(d) for d in a.get_all_dex()]

TARGET = "Lcom/sothree/slidinguppanel/SlidingUpPanelLayout;"
WANT = {"onMeasure", "setPanelHeight"}

for d in dexes:
    for c in d.get_classes():
        if c.get_name() != TARGET:
            continue
        for m in c.get_methods():
            if m.get_name() not in WANT:
                continue
            L.append(f"\n#### {m.get_name()} {m.get_descriptor()}")
            code = m.get_code()
            if code is None:
                L.append("  <no code>"); continue
            idx = 0
            for ins in code.get_bc().get_instructions():
                try:
                    txt = str(ins)  # androguard formats with operands
                except Exception as e:
                    txt = f"<err {e}>"
                L.append(f"  {idx:5d} {txt[:160]}")
                idx += ins.get_length()

open(OUT, "w").write("\n".join(L))
print(f"wrote {OUT}: {len(L)} lines")
