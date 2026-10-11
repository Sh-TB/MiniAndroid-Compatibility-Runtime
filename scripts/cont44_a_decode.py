#!/usr/bin/env python3
"""CONT44-A: decode F-NEW-306 csw regression.
Identify Lgi0; (original androidx class), its allocation chain, the Laj0;.n
isEmpty/getClass NPE site, and the Lch1;.s null-recv origin."""
import zipfile, sys
from androguard.core.dex import DEX

APK = '/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk'
z = zipfile.ZipFile(APK)
dexas = [DEX(z.read(n)) for n in z.namelist() if n.endswith('.dex')]

def iter_methods():
    for d in dexas:
        for c in d.get_classes():
            for m in c.get_methods():
                yield c, m

def find_class(cls):
    for d in dexas:
        for c in d.get_classes():
            if c.get_name() == cls:
                return c
    return None

def disasm(m, lo=0, hi=10**9):
    out = []
    code = m.get_code()
    if code is None:
        return out
    idx = 0
    for ins in code.get_bc().get_instructions():
        if lo <= idx <= hi:
            out.append(f"  pc={idx}: {ins.get_name()} {ins.get_output()}")
        idx += ins.get_length()
    return out

def full_class(cls):
    c = find_class(cls)
    if c is None:
        print(f"== class {cls}: NOT FOUND"); return
    print(f"== class {c.get_name()} extends {c.get_superclassname()} interfaces={[i for i in c.get_interfaces()]}")
    for f in c.get_fields():
        print(f"  field {f.get_name()} : {f.get_descriptor()}")
    for m in c.get_methods():
        code = m.get_code()
        sz = code.get_bc().get_length() if code else -1
        print(f"  method {m.get_name()}{m.get_descriptor()} size={sz}")

# ---- 1. Lgi0; identity ------------------------------------------------------
print("=" * 20, "1. Lgi0; class identity", "=" * 20)
full_class("Lgi0;")

print("\n-- Lgi0;.<init> full disasm --")
for c, m in iter_methods():
    if c.get_name() == "Lgi0;" and m.get_name() == "<init>":
        for l in disasm(m): print(l)

print("\n-- Lgi0;.<clinit> full disasm --")
for c, m in iter_methods():
    if c.get_name() == "Lgi0;" and m.get_name() == "<clinit>":
        for l in disasm(m): print(l)

# ---- 2. Who allocates Lgi0; (new-instance) ---------------------------------
print("\n" + "=" * 20, "2. Lgi0; allocation sites (new-instance)", "=" * 20)
for c, m in iter_methods():
    code = m.get_code()
    if code is None: continue
    idx = 0
    for ins in code.get_bc().get_instructions():
        if ins.get_name().startswith("new-instance") and "Lgi0;" in ins.get_output():
            print(f"ALLOC SITE {c.get_name()}->{m.get_name()}{m.get_descriptor()} pc={idx}: {ins.get_output()}")
        idx += ins.get_length()

# who invokes Lgi0;.<init> and Lgi0;.f readers/writers
print("\n-- invoke Lgi0;.<init> sites --")
for c, m in iter_methods():
    code = m.get_code()
    if code is None: continue
    idx = 0
    for ins in code.get_bc().get_instructions():
        o = ins.get_output()
        if ins.get_name().startswith("invoke") and "Lgi0;.<init>" in o:
            print(f"  {c.get_name()}->{m.get_name()} pc={idx}: {o}")
        idx += ins.get_length()

print("\n-- Lgi0;.f sget/iget readers & iput writers (any class) --")
for c, m in iter_methods():
    code = m.get_code()
    if code is None: continue
    idx = 0
    for ins in code.get_bc().get_instructions():
        o = ins.get_output()
        if ("Lgi0;->f" in o) and ins.get_name()[:3] in ("sge", "ige", "ipu", "spu"):
            print(f"  {c.get_name()}->{m.get_name()}{m.get_descriptor()} pc={idx}: {ins.get_name()} {o}")
        idx += ins.get_length()

# ---- 3. NPE sites ----------------------------------------------------------
print("\n" + "=" * 20, "3. NPE site Laj0;.n pc 90..115", "=" * 20)
for c, m in iter_methods():
    if c.get_name() == "Laj0;" and m.get_name() == "n":
        print(f"sig: {m.get_descriptor()}")
        for l in disasm(m, 85, 120): print(l)
        print("  --- try/cfg size:", m.get_code().get_bc().get_length())

print("\n-- Lch1; class identity + Lch1;.s pc 0..14 --")
c = find_class("Lch1;")
if c:
    print(f"class {c.get_name()} extends {c.get_superclassname()} interfaces={[i for i in c.get_interfaces()]}")
    for f in c.get_fields(): print(f"  field {f.get_name()} : {f.get_descriptor()}")
for c, m in iter_methods():
    if c.get_name() == "Lch1;" and m.get_name() == "s":
        print(f"Lch1;.s{m.get_descriptor()}:")
        for l in disasm(m, 0, 14): print(l)

print("\n-- Lx30;.n pc 78..92 (caller of Lch1;.s) --")
for c, m in iter_methods():
    if c.get_name() == "Lx30;" and m.get_name() == "n":
        print(f"Lx30;.n{m.get_descriptor()}:")
        for l in disasm(m, 78, 92): print(l)

# ---- 4. chain frames -------------------------------------------------------
print("\n" + "=" * 20, "4. propagation chain frames", "=" * 20)
for cls, name, lo, hi in [("Lmc0;", "Y", 0, 10**9), ("Lcj0;", "j0", 140, 155),
                          ("Ld91;", "c", 240, 320), ("Lh4;", "onMeasure", 70, 90)]:
    for c, m in iter_methods():
        if c.get_name() == cls and m.get_name() == name:
            print(f"-- {cls}->{name}{m.get_descriptor()} pc {lo}..{hi} --")
            for l in disasm(m, lo, hi): print(l)
            break
