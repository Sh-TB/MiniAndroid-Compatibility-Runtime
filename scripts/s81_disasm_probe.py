#!/usr/bin/env python3
"""s81_disasm_probe.py — disassemble one method of an APK's classes.dex and
print instructions around a target pc (S81 root-cause workflow)."""
import sys

from androguard.core.dex import DEX

apk = sys.argv[1]
cls = sys.argv[2]        # e.g. Lorg/debian/eugen/headingcalculator/CalculatorDisplay;
meth = sys.argv[3]       # e.g. updateValues
target_pc = int(sys.argv[4]) if len(sys.argv) > 4 else None

from androguard.core.bytecodes.apk import APK
a = APK(apk)
dex_data = a.get_dex()
d = DEX(dex_data)
for m in d.get_methods():
    if m.get_class_name() == cls.replace("/", ".") and m.get_name() == meth:
        code = m.get_code()
        if not code:
            continue
        print(f"method: {m.get_class_name()}.{m.get_name()} {m.get_descriptor()}")
        for ins in code.get_bc().get_instructions():
            op = ins.get_name()
            out = ins.get_output()
            pc = ins.get_pc()
            mark = " >>>" if (target_pc is not None and abs(pc - target_pc) <= 24) else "    "
            print(f"{mark} {pc:5d} {op:28s} {out[:90]}")
        break
