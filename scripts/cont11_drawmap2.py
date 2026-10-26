#!/usr/bin/env python3
"""CONT-11 W7 part 2: full bytecode of the canvas-wrap chain.
Targets: Lj7; (factory holder), Lt4;.dispatchDraw (register flow),
Luc0; (candidate CanvasHolder), callers of Lj7;.e / Lj7;.<init>."""
import zipfile, re
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
with zipfile.ZipFile(APK) as z:
    dexs = [DalvikVMFormat(z.read(n)) for n in sorted(z.namelist()) if re.match(r'classes\d*\.dex$', n)]

cls = {}
for d in dexs:
    for c in d.get_classes():
        cls[c.get_name()] = c

def ins(m):
    if not m.get_code(): return []
    out = []
    for i in m.get_code().get_bc().get_instructions():
        out.append(f"{i.get_name():16s} {i.get_output()}")
    return out

# --- Lj7; full class dump ---
c = cls.get('Lj7;')
print("=== Lj7; ===")
if c:
    print("super:", c.get_superclassname(), "ifaces:", list(c.get_interfaces()))
    for f in c.get_fields(): print("  field", f.get_name(), f.get_descriptor())
    for m in c.get_methods():
        print(f"  method {m.get_name()} {m.get_descriptor()} codelen={m.get_code() and m.get_code().get_length() or 0}")
        for l in ins(m): print("     ", l[:150])

# --- Lt4;.dispatchDraw full bytecode ---
c = cls.get('Lt4;')
print("\n=== Lt4;.dispatchDraw FULL ===")
for m in c.get_methods():
    if m.get_name() == 'dispatchDraw':
        for l in ins(m): print("   ", l[:160])

# --- Luc0; class dump ---
c = cls.get('Luc0;')
print("\n=== Luc0; ===")
if c:
    print("super:", c.get_superclassname(), "ifaces:", list(c.get_interfaces()))
    for f in c.get_fields(): print("  field", f.get_name(), f.get_descriptor())
    for m in c.get_methods():
        print(f"  method {m.get_name()} {m.get_descriptor()} codelen={m.get_code() and m.get_code().get_length() or 0}")
        if m.get_name() in ('g','<init>') and m.get_code() and m.get_code().get_length() < 400:
            for l in ins(m): print("     ", l[:150])

# --- callers of Lj7;.e ---
print("\n=== callers of Lj7;->e(Ldi;)V ===")
n = 0
for cn, c in cls.items():
    for m in c.get_methods():
        for i in (m.get_code().get_bc().get_instructions() if m.get_code() else []):
            s = i.get_output()
            if 'Lj7;->e(Ldi;)V' in s or ('Lj7;' in s and '-><init>' in s):
                print(f"  {cn}->{m.get_name()}{m.get_descriptor()}")
                print(f"      {i.get_name()} {s[:140]}")
                n += 1
                if n > 15: break
        if n > 15: break
    if n > 15: break
