#!/usr/bin/env python3
"""CONT-36 Phase 3d: decode Lce1 (AndroidParagraph, R8'd) — the paragraph
paint method body: what does it call to paint? Plus Lce1's Canvas-typed
methods and every invoke of android.graphics.Paint.set* during paint."""
import zipfile, sys
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk"
z = zipfile.ZipFile(APK)
d = DEX(z.read("classes.dex"))

TARGET = "Lce1;"
methods = []
for c in d.get_classes():
    if c.get_name() != TARGET:
        continue
    for m in c.get_methods():
        methods.append(m)

print(f"Lce1 methods: {len(methods)}")
for m in methods:
    print(f"  {m.get_name()} {m.get_descriptor()}")

# Disassemble any method whose descriptor mentions Canvas (paint family)
for m in methods:
    desc = m.get_descriptor()
    if "Landroid/graphics/Canvas;" not in desc:
        continue
    code = m.get_code()
    if not code:
        print(f"--- {m.get_name()} {desc}: abstract/no code")
        continue
    print(f"--- {m.get_name()} {desc} regs={code.get_registers_size()} ---")
    pc = 0
    for ins in m.get_instructions():
        nm = ins.get_name()
        out = ins.get_output()
        if "invoke" in nm or "iget" in nm or nm.startswith("const") or \
           "sget" in nm or nm.startswith("return") or "check-cast" in nm:
            print(f"  pc={pc} {nm} {out[:130]}")
        pc += ins.get_length()
