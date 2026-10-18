#!/usr/bin/env python3
"""CONT-94: decode s2.checkSystemBarColors + s2.onBecomeFullyVisible receiver
lineage for the H(Z Z Z)V call sites (the synthetic-activity identity break)."""
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat

a = APK("upload/telegram_official.apk")
d = None
for dn in a.get_dex_names():
    r = a.get_file(dn)
    if b"checkSystemBarColors" not in r:
        continue
    cand = DalvikVMFormat(r)
    if any(c.get_name() == "Lorg/telegram/ui/ActionBar/s2;" for c in cand.get_classes()):
        d = cand
        break
assert d
s2 = next(c for c in d.get_classes() if c.get_name() == "Lorg/telegram/ui/ActionBar/s2;")

def disasm(m, limit=200):
    out = []
    addr = 0
    for ins in m.get_code().get_bc().get_instructions():
        out.append((addr, ins.get_name(), ins.get_output()))
        addr += ins.get_length()
        if limit and len(out) >= limit:
            break
    return out

for m in s2.get_methods():
    if m.get_name() in ("checkSystemBarColors", "onBecomeFullyVisible"):
        print("=== %s %s regs=%d ===" % (m.get_name(), m.get_descriptor(),
                                         m.get_code().get_registers_size()))
        for addr, op, o in disasm(m, 60):
            print("  %04d: %s %s" % (addr, op, o))
        print()
