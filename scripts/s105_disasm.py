#!/usr/bin/env python3
"""s105_disasm.py — disassemble one method of an APK's classes.dex
(androguard 4.x API). Usage: python3 scripts/s105_disasm.py APK CLASS METHOD [max_pc]"""
import sys
from androguard.core.apk import APK
from androguard.core.dex import DEX

apk, cls_name, meth_name = sys.argv[1], sys.argv[2], sys.argv[3]
max_pc = int(sys.argv[4]) if len(sys.argv) > 4 else None

a = APK(apk)
d = DEX(a.get_dex())
lines = []
found = 0
for cls in d.get_classes():
    if cls.get_name() != cls_name:
        continue
    for m in cls.get_methods():
        if m.get_name() != meth_name:
            continue
        found += 1
        code = m.get_code()
        lines.append("method: %s  code=%s" % (m.get_descriptor(), code is not None))
        if not code:
            continue
        for ins in code.get_bc().get_instructions():
            pc = getattr(ins, "_pc", None)
            if pc is None:
                pc = getattr(ins, "pc", None)
            if pc is None:
                # androguard 4.x: track manually via instruction length
                try:
                    pc = ins.get_offset()  # may not exist
                except Exception:
                    pc = None
            if max_pc is None or (pc is not None and pc <= max_pc):
                lines.append("%5s %-26s %s" % (pc, ins.get_name(), ins.get_output()[:100]))
print("found=%d" % found)
print("\n".join(lines[:120]))
