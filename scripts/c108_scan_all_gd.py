#!/usr/bin/env python3
"""CONT-108: whole-APK scan for getDrawable invoke sites + const 0x7f08007f users.
Output: run/c108/oc_getdrawable_all.txt
"""
import sys, logging
logging.getLogger("androguard").setLevel(logging.ERROR)
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = sys.argv[1] if len(sys.argv) > 1 else "upload/opencalculator_53.apk"
OUT = "run/c108/oc_getdrawable_all.txt"
L = []

a = APK(APK_PATH)
dexes = [DEX(d) for d in a.get_all_dex()]

for di, d in enumerate(dexes):
    for c in d.get_classes():
        for m in c.get_methods():
            code = m.get_code()
            if code is None:
                continue
            idx = 0
            has_const = False
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                try:
                    if op.startswith("const"):
                        ops = ins.get_operands()
                        for o in ops:
                            if o[0] == 0 and isinstance(o[1], int) and o[1] == 0x7f08007f:
                                has_const = True
                    if "invoke" in op:
                        operands = ins.get_operands()
                        meth = operands[-1][2]
                        if isinstance(meth, str) and "->getDrawable(" in meth:
                            L.append(f"[GD] {c.get_name()}->{m.get_name()} @{idx} {meth}"
                                     + ("   <== CONST 0x7f08007f" if has_const else ""))
                except Exception:
                    pass
                idx += ins.get_length()

open(OUT, "w").write("\n".join(L))
print(f"wrote {OUT}: {len(L)} sites")
