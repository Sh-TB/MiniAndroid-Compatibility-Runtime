#!/usr/bin/env python3
"""CONT-36 Phase 3g: identify Ln3 (the draw-dispatch holder) — super,
interfaces, fields, and the bodies of .h/.n/.q/.d/.e; plus Lmc0;.i (the
LayoutNode draw walk entry) — to find where the walk stops before text."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk"
z = zipfile.ZipFile(APK)
d = DEX(z.read("classes.dex"))

for c in d.get_classes():
    if c.get_name() not in ("Ln3;", "Lmc0;"):
        continue
    print(f"=== class {c.get_name()} ===")
    try:
        print("  super:", c.get_superclassname())
        ifaces = c.get_interfaces()
        print("  ifaces:", ifaces)
    except Exception as e:
        print("  meta err:", e)
    for f in c.get_fields():
        print("  field:", f.get_name(), f.get_descriptor())
    want = set()
    if c.get_name() == "Ln3;":
        want = {"h", "n", "q", "d", "e", "<clinit>"}
    else:
        want = {"i"}
    for m in c.get_methods():
        if m.get_name() not in want:
            continue
        code = m.get_code()
        if not code:
            print(f"  --- {m.get_name()} {m.get_descriptor()}: no code")
            continue
        print(f"  --- {m.get_name()} {m.get_descriptor()} "
              f"regs={code.get_registers_size()} ---")
        pc = 0
        for ins in m.get_instructions():
            nm = ins.get_name()
            out = ins.get_output()
            if ("invoke" in nm or "iget" in nm or "sget" in nm or
                    nm.startswith("const") or nm.startswith("return") or
                    "check-cast" in nm or nm.startswith("if") or
                    "new-instance" in nm):
                print(f"    pc={pc} {nm} {out[:120]}")
            pc += ins.get_length()
    print()
