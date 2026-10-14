#!/usr/bin/env python3
"""CONT-64 W1 — F-NEW-267 residual leg decode: the compose hit-test walk.

The [TOUCHWIN-BRIDGE] trace shows the DOWN dispatched into Lt4;.dispatchTouchEvent
→ coordinates walk (Loh;.a) → matrix values consumed (Lg5;.D) → hit-test
(Lzs0;.k) → filter dispatch (Las0;.t, size=0 EMPTY).

This script disassembles the pure-DEX hit-test walk so the bounds-source law
comes from the LIVE APP DEX, not from guessing:
  - Lzs0;.k / Lzs0;.i — the hit-test result walk (which fields hold bounds?)
  - Loh;.a — the coordinates→matrix walk (which receiver's fields?)
  - Las0;.t — the filter dispatch loop
  - the LayoutNode/ coordinator classes these consult (follow field types)
"""
import sys, zipfile
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"

JOBS = [
    # (class, method, max_insns)  max_insns=None → all
    ("Lzs0;", "k", 200),
    ("Lzs0;", "i", 120),
    ("Loh;", "a", 260),
    ("Lg5;", "D", 160),
    ("Las0;", "t", 160),
]

def load_classes(apk):
    z = zipfile.ZipFile(apk)
    out = {}
    for n in sorted(x for x in z.namelist()
                    if x.startswith("classes") and x.endswith(".dex")):
        d = DalvikVMFormat(z.read(n))
        for c in d.get_classes():
            out[c.get_name()] = c
    return out

def disasm_method(c, meth, max_insns):
    for m in c.get_methods():
        if m.get_name() != meth:
            continue
        print(f"--- {c.get_name()}.{m.get_name()}"
              f"({', '.join(t.get_type() for t in m.get_instructions() and []) or ''})"
              f" regs={m.get_code().registers_size}")
        n = 0
        for ins in m.get_instructions():
            op = ins.get_name()
            out = f"  {ins.get_idx():04x}: {op:<28} {ins.get_output()}"
            print(out[:200])
            n += 1
            if max_insns and n >= max_insns:
                print("  ... (truncated)")
                break
        return True
    return False

def main():
    classes = load_classes(APK)
    print(f"classes loaded: {len(classes)}")
    for cls, meth, lim in JOBS:
        c = classes.get(cls)
        print("=" * 100)
        if not c:
            print(f"CLASS {cls} NOT FOUND")
            continue
        if not disasm_method(c, meth, lim):
            print(f"METHOD {cls}.{meth} NOT FOUND; methods="
                  f"{[m.get_name() for m in c.get_methods()][:30]}")

if __name__ == "__main__":
    main()
