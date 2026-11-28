#!/usr/bin/env python3
"""T279 P4 — disassemble the Compose convertMeasureSpec ISE throw site.

Extracts classes*.dex from the APK, finds
Landroidx/compose/ui/platform/AndroidComposeView;.convertMeasureSpec-I7RO_PI
and prints the instruction listing around the throwing pc (29).
"""
import sys
import zipfile
from pathlib import Path

from androguard.core.dex import DEX

APK = Path(sys.argv[1] if len(sys.argv) > 1 else
           "/home/z/my-project/upload/fdroid_batch/ac.stresa.uturn_22.apk")
CLS = "Landroidx/compose/ui/platform/AndroidComposeView;"
METH = sys.argv[2] if len(sys.argv) > 2 else "convertMeasureSpec"


def main():
    with zipfile.ZipFile(APK) as z:
        dexes = [n for n in z.namelist()
                 if n.startswith("classes") and n.endswith(".dex")]
        print(f"[disasm] {APK.name}: {len(dexes)} dex files")
        for name in dexes:
            d = DEX(z.read(name))
            for m in d.get_methods():
                if m.get_class_name() == CLS and METH in m.get_name():
                    code = m.get_code()
                    if code is None:
                        print(f"[disasm] {m.get_name()} {m.get_descriptor()}"
                              " abstract/native")
                        continue
                    print(f"=== {name} {m.get_name()} {m.get_descriptor()} "
                          f"regs={code.get_registers_size()} "
                          f"ins={code.get_ins_size()} ===")
                    off = 0
                    for ins in code.get_bc().get_instructions():
                        op = ins.get_name()
                        if op in ("nop", "nop-payload"):
                            off += ins.get_length()
                            continue
                        if abs(off - 29) < 26:
                            print(f"  pc={off:4d} {op:28s} "
                                  f"{ins.get_output()[:90]}")
                        off += ins.get_length()


if __name__ == "__main__":
    main()
