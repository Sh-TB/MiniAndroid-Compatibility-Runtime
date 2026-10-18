#!/usr/bin/env python3
"""CONT-94: dump z0 + H receiver lineage + field-writers of the null sources."""
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat

a = APK("upload/telegram_official.apk")
d = None
for dn in a.get_dex_names():
    r = a.get_file(dn)
    if b"LaunchActivity" not in r:
        continue
    cand = DalvikVMFormat(r)
    if any(c.get_name() == "Lorg/telegram/ui/LaunchActivity;" for c in cand.get_classes()):
        d = cand
        break
assert d, "LaunchActivity dex not found"
la = next(c for c in d.get_classes() if c.get_name() == "Lorg/telegram/ui/LaunchActivity;")

def disasm(m):
    out = []
    addr = 0
    for ins in m.get_code().get_bc().get_instructions():
        out.append((addr, ins.get_name(), ins.get_output()))
        addr += ins.get_length()
    return out

for m in la.get_methods():
    if m.get_name() == "z0":
        print("=== z0 %s regs=%d ===" % (m.get_descriptor(), m.get_code().get_registers_size()))
        for addr, op, o in disasm(m):
            print("  %04d: %s %s" % (addr, op, o))

# fields of e4 (drawer layout container) that z0/H read; and k5 parentLayout field
print("\n=== k5 fields (parentLayout holder) ===")
k5 = next((c for c in d.get_classes() if c.get_name() == "Lorg/telegram/ui/ActionBar/k5;"), None)
if k5:
    for f in k5.get_fields():
        print("  %s : %s" % (f.get_name(), f.get_descriptor()))

print("\n=== s2 fields ===")
s2 = next((c for c in d.get_classes() if c.get_name() == "Lorg/telegram/ui/ActionBar/s2;"), None)
if s2:
    for f in s2.get_fields():
        print("  %s : %s" % (f.get_name(), f.get_descriptor()))

print("\n=== getParentLayout implementations ===")
for c in d.get_classes():
    if c.get_name() in ("Lorg/telegram/ui/ActionBar/k5;", "Lorg/telegram/ui/ActionBar/s2;"):
        for m in c.get_methods():
            if m.get_name() == "getParentLayout":
                print("--- %s.%s %s ---" % (c.get_name(), m.get_name(), m.get_descriptor()))
                for addr, op, o in disasm(m):
                    print("  %04d: %s %s" % (addr, op, o))
