#!/usr/bin/env python3
"""CONT-108: find ALL invoke sites of getDrawable / SlidingUpPanelLayout in the
opencalculator app package (com.darkempire78.*) and print caller class->method.
Output: run/c108/oc_getdrawable_sites.txt
"""
import sys, logging
logging.getLogger("androguard").setLevel(logging.ERROR)
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = sys.argv[1] if len(sys.argv) > 1 else "upload/opencalculator_53.apk"
OUT = "run/c108/oc_getdrawable_sites.txt"
L = []

a = APK(APK_PATH)
dexes = [DEX(d) for d in a.get_all_dex()]

APP = "Lcom/darkempire78"
for di, d in enumerate(dexes):
    for c in d.get_classes():
        if not c.get_name().startswith(APP):
            continue
        for m in c.get_methods():
            code = m.get_code()
            if code is None:
                continue
            idx = 0
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                if "invoke" in op:
                    try:
                        operands = ins.get_operands()
                        meth = operands[-1][2]
                        if isinstance(meth, str) and (
                            "getDrawable" in meth or "SlidingUpPanelLayout" in meth
                            or "below_shadow" in meth or "setPanelHeight" in meth
                            or "addPanelSlideListener" in meth or "setShadowDrawable" in meth
                        ):
                            L.append(f"{c.get_name()}->{m.get_name()} @{idx:5d} {op} {meth}")
                    except Exception:
                        pass
                idx += ins.get_length()

open(OUT, "w").write("\n".join(L))
print(f"wrote {OUT}: {len(L)} sites")
