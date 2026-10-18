#!/usr/bin/env python3
"""CONT-94 Telegram-first wave: decode LaunchActivity.H null-receiver NPE.

Evidence question (honest, fixture-first):
  [SYNTH-EXC] f141-null-recv (deferred): NullPointerException
    "Attempt to invoke virtual method 'Lorg/telegram/ui/ActionBar/ActionBarLayout;.w'
     on a null object reference" at Lorg/telegram/ui/LaunchActivity;.H pc=248
  uncaught 3x at LaunchActivity.onCreate invoke_pc=751/994/1011 -> APP BOUNDARY.

Deliverables:
  1. H bytecode around pc=248: which iget field feeds the null receiver.
  2. All writers (iput/sput) of that field anywhere in the dex that owns
     LaunchActivity — plus the declaring class of the field.
  3. onCreate call sites pc=751/994/1011 — which method each invokes.
"""
import sys
from androguard.core.bytecodes.apk import APK

APK_PATH = "upload/telegram_official.apk"
TARGET = "Lorg/telegram/ui/LaunchActivity;"

a = APK(APK_PATH)
dex_with_target = None
for dex_name in a.get_dex_names():
    raw = a.get_file(dex_name)
    # cheap contains-check before full parse: 'LaunchActivity' string in dex
    if b"LaunchActivity" not in raw:
        continue
    from androguard.core.bytecodes.dvm import DalvikVMFormat as DEX
    d = DEX(raw)
    if any(c.get_name() == TARGET for c in d.get_classes()):
        dex_with_target = (dex_name, d)
        break

if not dex_with_target:
    print("FATAL: LaunchActivity not found in any dex")
    sys.exit(1)

dex_name, d = dex_with_target
print("LaunchActivity found in dex: %s" % dex_name)

la = None
for c in d.get_classes():
    if c.get_name() == TARGET:
        la = c
        break

print("-- LaunchActivity fields (type ActionBarLayout) --")
bar_fields = []
for f in la.get_fields():
    if "ActionBarLayout" in f.get_descriptor():
        print("  field %s : %s access=%s" % (f.get_name(), f.get_descriptor(), f.get_access_flags_string()))
        bar_fields.append(f.get_name())

def disasm_range(m, lo, hi):
    """disassemble instructions with addr in [lo,hi)"""
    out = []
    code = m.get_code()
    bc = code.get_bc()
    idx = 0
    addr = 0
    for ins in bc.get_instructions():
        op = ins.get_name()
        outp = "  %04d: %s %s" % (addr, op, ins.get_output())
        if lo <= addr < hi:
            out.append(outp)
        sz = ins.get_length()
        addr += sz
    return out

print("\n-- LaunchActivity.H --")
for m in la.get_methods():
    if m.get_name() != "H":
        continue
    code = m.get_code()
    print("method H regs=%d ins=%d" % (code.get_registers_size(), code.get_ins_size()))
    for l in disasm_range(m, 0, 400):
        print(l)

print("\n-- LaunchActivity.onCreate call sites 700..1100 --")
for m in la.get_methods():
    if m.get_name() != "onCreate":
        continue
    for l in disasm_range(m, 700, 1100):
        print(l)

print("\n-- writers of ActionBarLayout-typed fields across dex (classes named Lorg/telegram/ui/LaunchActivity or superclasses) --")
# Who writes any field named like the bar_fields anywhere? (limit: field names from LaunchActivity)
names = set(bar_fields)
for c in d.get_classes():
    cn = c.get_name()
    if cn != TARGET:
        continue
    for m in c.get_methods():
        code = m.get_code()
        if not code:
            continue
        bc = code.get_bc()
        addr = 0
        for ins in bc.get_instructions():
            op = ins.get_name()
            if op.startswith("iput") and len(names) > 0:
                o = ins.get_output()
                for nm in names:
                    if nm in o:
                        print("  writer: %s.%s pc=%d: %s %s" % (cn, m.get_name(), addr, op, o))
            addr += ins.get_length()
