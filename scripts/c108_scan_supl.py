#!/usr/bin/env python3
"""CONT-108: disassemble SlidingUpPanelLayout.onMeasure + setPanelHeight paths.
Output: run/c108/oc_supl_onmeasure.txt
"""
import sys, logging
logging.getLogger("androguard").setLevel(logging.ERROR)
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = sys.argv[1] if len(sys.argv) > 1 else "upload/opencalculator_53.apk"
OUT = "run/c108/oc_supl_onmeasure.txt"
L = []

a = APK(APK_PATH)
dexes = [DEX(d) for d in a.get_all_dex()]

TARGET = "Lcom/sothree/slidinguppanel/SlidingUpPanelLayout;"
WANT = {"onMeasure", "setPanelHeight", "onSizeChanged", "onLayout"}

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
                op = ins.get_name()
                try:
                    operands = ins.get_operands()
                    ops = []
                    for o in operands:
                        if o[0] == 0:
                            ops.append(repr(o[1]))
                        elif isinstance(o[2], str):
                            ops.append(o[2])
                        else:
                            ops.append(f"v{o[1]}")
                    L.append(f"  {idx:5d} {op:24s} {', '.join(ops)[:150]}")
                except Exception as e:
                    L.append(f"  {idx:5d} <err {e}>")
                idx += ins.get_length()

open(OUT, "w").write("\n".join(L))
print(f"wrote {OUT}: {len(L)} lines")
