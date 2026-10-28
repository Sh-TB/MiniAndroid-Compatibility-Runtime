#!/usr/bin/env python3
"""cont49_tiny1.py — root-cause the ConstraintLayout.onLayout NPE:
'Attempt to invoke virtual method Lx/d;.r on a null object reference'
at Landroidx/constraintlayout/widget/ConstraintLayout;.onLayout pc=43.
Decode the APK bytecode: which iget feeds the receiver, which field is null,
and where that field should have been set (ctor / onFirstLayout)."""
import sys
from loguru import logger
logger.remove()
from androguard.core.bytecodes.dvm import DalvikVMFormat as DEX

APK_DEX = sys.argv[1] if len(sys.argv) > 1 else None
TARGET = "Landroidx/constraintlayout/widget/ConstraintLayout;"

d = DEX(open(APK_DEX, "rb").read())
cls = next((c for c in d.get_classes() if c.get_name() == TARGET), None)
if not cls:
    print("CLASS-NOT-FOUND", TARGET)
    sys.exit(1)

print("=== fields ===")
for f in cls.get_fields():
    print(" ", f.get_name(), f.get_descriptor())

print("=== onLayout ===")
m = next((m for m in cls.get_methods() if m.get_name() == "onLayout"), None)
if m:
    idx = 0
    for ins in m.get_instructions():
        op = ins.get_name()
        out = ins.get_output()
        mark = " <<<" if idx in (41, 42, 43, 44) else ""
        if idx >= 30:
            print(f"  pc={idx:4d} {op:28s} {out}{mark}")
        idx += ins.get_length()
