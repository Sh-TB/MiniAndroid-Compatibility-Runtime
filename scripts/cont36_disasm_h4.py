#!/usr/bin/env python3
"""CONT-36 Phase 3c: disassemble Lh4;.dispatchDraw (AndroidComposeView, R8'd)
from composeStopwatch — find whether the draw goes direct to the Canvas arg
or into a RenderNode/GraphicsLayer record(); and who calls Lkd1.draw*."""
import zipfile, sys
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk"
z = zipfile.ZipFile(APK)
d = DEX(z.read("classes.dex"))

TARGETS = [("Lh4;", "dispatchDraw"), ("Lkd1;", "drawText")]

for tcls, tname in TARGETS:
    for c in d.get_classes():
        if c.get_name() != tcls:
            continue
        for m in c.get_methods():
            if m.get_name() != tname:
                continue
            code = m.get_code()
            if not code:
                print(f"{tcls}.{tname}: NO CODE")
                continue
            print(f"=== {tcls}.{tname} {m.get_descriptor()} "
                  f"regs={code.get_registers_size()} ===")
            pc = 0
            for ins in m.get_instructions():
                nm = ins.get_name()
                out = ins.get_output()
                keep = ("invoke" in nm or nm.startswith("const")
                        or "sget" in nm or "iget" in nm
                        or nm.startswith("if") or nm.startswith("return")
                        or "new-instance" in nm or "check-cast" in nm)
                if keep:
                    print(f"pc={pc} {nm} {out[:150]}")
                pc += ins.get_length()
            print()

# who calls Lkd1;.drawText / Lkd1;.draw* (the Compose AndroidCanvas impl)?
print("== callers of Lkd1;.draw* ==")
callers = {}
for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                if "invoke" not in ins.get_name():
                    continue
                out = ins.get_output()
                if out.startswith("Lkd1;->draw"):
                    meth = out.split("->")[1].split(":")[0].split("(")[0]
                    callers.setdefault(meth, []).append(
                        f"{m.get_class_name()}.{m.get_name()}")
        except Exception:
            continue
for meth, cs in sorted(callers.items()):
    uniq = sorted(set(cs))
    print(f"  Lkd1;.{meth}: {len(uniq)} callers, e.g. {uniq[:6]}")
