#!/usr/bin/env python3
"""CONT-108: find setVisibility(4/8) invoke sites inside the SlidingUpPanelLayout
fork + l1.* helpers, with the enclosing method and surrounding consts.
Output: run/c108/oc_supl_setvis.txt
"""
import sys, logging
logging.getLogger("androguard").setLevel(logging.ERROR)
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = sys.argv[1] if len(sys.argv) > 1 else "upload/opencalculator_53.apk"
OUT = "run/c108/oc_supl_setvis.txt"
L = []

a = APK(APK_PATH)
dexes = [DEX(d) for d in a.get_all_dex()]

TARGETS = ("Lcom/sothree/slidinguppanel/SlidingUpPanelLayout;",
           "Ll1/a;", "Ll1/b;", "Ll1/c;", "Ll1/d;", "Ll1/e;", "Ll1/f;", "Ll1/g;")
for d in dexes:
    for c in d.get_classes():
        if c.get_name() not in TARGETS:
            continue
        for m in c.get_methods():
            code = m.get_code()
            if code is None:
                continue
            idx = 0
            consts = {}
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                try:
                    if op.startswith("const"):
                        for o in ins.get_operands():
                            if o[0] == 0 and isinstance(o[1], int):
                                consts[idx] = o[1]
                    if "invoke" in op:
                        meth = ins.get_operands()[-1][2]
                        if isinstance(meth, str) and "setVisibility" in meth:
                            recent = [v for k, v in consts.items() if 0 <= idx - k <= 40]
                            L.append(f"{c.get_name()}->{m.get_name()} @{idx} {meth}"
                                     f"  recent_consts={recent[-6:]}")
                except Exception:
                    pass
                idx += ins.get_length()

open(OUT, "w").write("\n".join(L))
print(f"wrote {OUT}: {len(L)} sites")
