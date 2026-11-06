#!/usr/bin/env python3
"""S188: decode the Compose RuntimeException root in queens/tarok.
l0/c.a pc=815 constructs+throws RuntimeException; h0/j.<init> pc=0x21 unwound.
Extract the real message + calling context from the DEX."""
from androguard.misc import AnalyzeAPK
import sys

APK = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/z/my-project/evidence/s188/first_renders/runs/run_store_com.sidhant.queens/data/app/com.sidhant.queens/base.apk"
CLASSES = ["Ll0/c;", "Lh0/j;", "Lg0/f;"]
PC_HIT = {"Ll0/c;": 815, "Lh0/j;": 0x21}

a, d, dx = AnalyzeAPK(APK)

def dump_around(meth, pc_hit, radius=24):
    m = meth.get_method()
    print("=" * 78)
    print("METHOD", m.get_class_name(), "->", m.get_name(), m.get_descriptor())
    code = m.get_code()
    idx = 0
    keep = []
    for ins in code.get_bc().get_instructions():
        op = ins.get_name()
        if abs(idx - pc_hit) <= radius:
            keep.append(f"  @{idx:6d} {op} {ins.get_output()}")
        idx += ins.get_length()
        if idx > pc_hit + radius:
            break
    print("\n".join(keep))

for m in dx.get_methods():
    if m.is_external():
        continue
    meth = m.get_method()
    cls = meth.get_class_name()
    if cls not in CLASSES:
        continue
    if cls == "Ll0/c;" and meth.get_name() == "a":
        dump_around(m, PC_HIT[cls], radius=30)
    elif cls == "Lh0/j;" and meth.get_name() == "<init>":
        dump_around(m, PC_HIT[cls], radius=40)
    elif cls == "Lg0/f;" and meth.get_name() == "onCreate":
        # find the invoke that reaches h0/j pc=0x2e8
        code = meth.get_code()
        idx = 0
        for ins in code.get_bc().get_instructions():
            op = ins.get_name()
            if 0x2c0 <= idx <= 0x300 and ("invoke" in op or "const" in op):
                print(f"[g0/f.onCreate] @{idx:6d} {op} {ins.get_output()}")
            idx += ins.get_length()
            if idx > 0x300:
                break
