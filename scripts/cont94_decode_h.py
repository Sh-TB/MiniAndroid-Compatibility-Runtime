#!/usr/bin/env python3
"""CONT-94: enumerate ALL LaunchActivity.H overloads + every ActionBarLayout;.w()
call site with receiver register lineage; also A0 fragment-stack paths."""
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK_PATH = "upload/telegram_official.apk"
TARGET = "Lorg/telegram/ui/LaunchActivity;"

a = APK(APK_PATH)
raw = None
for dex_name in a.get_dex_names():
    r = a.get_file(dex_name)
    if b"LaunchActivity" in r:
        d = DalvikVMFormat(r)
        if any(c.get_name() == TARGET for c in d.get_classes()):
            raw = r
            break
assert raw
d = DalvikVMFormat(raw)
la = next(c for c in d.get_classes() if c.get_name() == TARGET)

def full_disasm(m):
    out = []
    addr = 0
    for ins in m.get_code().get_bc().get_instructions():
        out.append((addr, ins.get_name(), ins.get_output()))
        addr += ins.get_length()
    return out

hs = [m for m in la.get_methods() if m.get_name() == "H"]
print("H overloads: %d" % len(hs))
for m in hs:
    code = m.get_code()
    print("\n=== H %s regs=%d ins=%d insns=%d ===" % (
        m.get_descriptor(), code.get_registers_size(), code.get_ins_size(),
        code.get_insns_size()))
    w_sites = []
    for addr, op, o in full_disasm(m):
        if "ActionBarLayout;->w(" in o:
            w_sites.append((addr, op, o))
    for addr, op, o in w_sites:
        print("  w() call @%d: %s %s" % (addr, op, o))

# also map caller frame info: who calls H (invoke in LaunchActivity.onCreate/other)
print("\n=== callers of LaunchActivity;->H within LaunchActivity ===")
hdescs = set(m.get_descriptor() for m in hs)
for m in la.get_methods():
    code = m.get_code()
    if not code:
        continue
    addr = 0
    for ins in code.get_bc().get_instructions():
        o = ins.get_output()
        if ins.get_name().startswith("invoke") and any(
                ("LaunchActivity;->H" + d.replace("(", "\\(")) in o for d in hdescs):
            print("  %s.%s @%d: %s %s" % (la.get_name(), m.get_name(), addr, ins.get_name(), o))
        addr += ins.get_length()

# print the FULL disasm of each H overload into a file for reference
with open("run/cont94/h_overloads_full.txt", "w") as f:
    for m in hs:
        f.write("=== %s %s ===\n" % (m.get_name(), m.get_descriptor()))
        for addr, op, o in full_disasm(m):
            f.write("  %04d: %s %s\n" % (addr, op, o))
        f.write("\n")
print("\nfull disasm -> run/cont94/h_overloads_full.txt")

# A0: fragment/layer construction order
a0 = next(m for m in la.get_methods() if m.get_name() == "A0")
with open("run/cont94/a0_full.txt", "w") as f:
    for addr, op, o in full_disasm(a0):
        f.write("  %04d: %s %s\n" % (addr, op, o))
print("A0 disasm -> run/cont94/a0_full.txt")
