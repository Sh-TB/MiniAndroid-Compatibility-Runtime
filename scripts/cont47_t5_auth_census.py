#!/usr/bin/env python3
"""CONT-47 T5 TELEGRAM: all-dex census of auth/intro class references.
Finds who constructs/references IntroActivity / LoginActivity / a0t (R8
renames included via string pool hit). ZERO-LOG: census rows only."""
import logging, zipfile, sys
logging.disable(logging.CRITICAL)
from loguru import logger as _lg
_lg.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/upload/telegram_official.apk"
TARGETS = ("Lorg/telegram/ui/IntroActivity;",
           "Lorg/telegram/ui/LoginActivity;",
           "Lorg/telegram/ui/PasscodeActivity;")

# pass 1: which dexes declare the target classes (cheap string-pool check)
z = zipfile.ZipFile(APK)
dexes = [n for n in z.namelist() if n.endswith(".dex")]
for dn in dexes:
    b = z.read(dn)
    if b"IntroActivity" not in b and b"LoginActivity" not in b:
        continue
    d = DEX(b)
    for c in d.get_classes():
        if c.get_name() in TARGETS:
            print(f"DECL {c.get_name()} in {dn}")
    # pass 2: refs
    for c in d.get_classes():
        cn = c.get_name()
        for m in c.get_methods():
            code = m.get_code()
            if not code:
                continue
            for ins in code.get_bc().get_instructions():
                oname = ins.get_name()
                if not (oname.startswith("new-instance") or
                        oname.startswith("const-class") or
                        oname.startswith("check-cast") or
                        oname.startswith("invoke-")):
                    continue
                try:
                    ops = ins.get_operands(0)
                except Exception:
                    continue
                for o in ops:
                    if len(o) >= 3 and isinstance(o[2], str) and o[2] in TARGETS:
                        print(f"REF {o[2]} <- {cn}.{m.get_name()} [{dn}] op={oname}")
                        break
print("T5-CENSUS-DONE")
