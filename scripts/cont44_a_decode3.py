#!/usr/bin/env python3
"""CONT44-A part 3: pin the Lch1; allocation contract + Lgi0;(tag=0xd DepthSortedSet)
allocation site + Lmc0;.E writer path."""
import zipfile
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

def disasm(m, lo=0, hi=10**9):
    out = []
    code = m.get_code()
    if code is None: return out
    idx = 0
    for ins in code.get_bc().get_instructions():
        if lo <= idx <= hi:
            out.append(f"  pc={idx}: {ins.get_name()} {ins.get_output()}")
        idx += ins.get_length()
    return out

def dump(cls, name, lo=0, hi=10**9, nth=0):
    k = 0
    for c, m in iter_methods():
        if c.get_name() == cls and m.get_name() == name:
            if k == nth:
                print(f"-- {cls}->{name}{m.get_descriptor()} [{lo}..{hi}] --")
                for l in disasm(m, lo, hi): print(l)
                return
            k += 1
    print(f"-- {cls}->{name}: NOT FOUND --")

print("== 1. Lch1; identity ==")
c = find_class("Lch1;")
print(f"Lch1; extends {c.get_superclassname()} ifaces={[i for i in c.get_interfaces()]}")
for m in c.get_methods(): print(f"  method {m.get_name()}{m.get_descriptor()} size={m.get_code().get_bc().get_length() if m.get_code() else -1}")

print("\n== 2. ALL Lch1;.<init> invoke-direct sites ==")
for c, m in iter_methods():
    code = m.get_code()
    if code is None: continue
    idx = 0
    for ins in code.get_bc().get_instructions():
        o = ins.get_output()
        if ins.get_name().startswith("invoke") and "Lch1;-><init>" in o:
            print(f"  {c.get_name()}->{m.get_name()}{m.get_descriptor()} pc={idx}: {o}")
        idx += ins.get_length()

print("\n== 3. external callers of Lch1; methods (non-Lch1 classes) ==")
n = 0
for c, m in iter_methods():
    if c.get_name() == "Lch1;": continue
    code = m.get_code()
    if code is None: continue
    idx = 0
    for ins in code.get_bc().get_instructions():
        o = ins.get_output()
        if ins.get_name().startswith("invoke") and "Lch1;->" in o and "<init>" not in o:
            if n < 25:
                print(f"  {c.get_name()}->{m.get_name()}{m.get_descriptor()} pc={idx}: {o}")
            n += 1
        idx += ins.get_length()
print(f"  total external call sites: {n}")

print("\n== 4. identities: Lzv; Lju0; Lpr; Ldj; Lnu0; Ld8; ==")
for cls in ("Lzv;", "Lju0;", "Lpr;", "Ldj;", "Lnu0;", "Ld8;"):
    cc = find_class(cls)
    if cc is None:
        print(f"{cls}: NOT FOUND"); continue
    strs = set()
    for m in cc.get_methods():
        code = m.get_code()
        if not code: continue
        for ins in code.get_bc().get_instructions():
            if ins.get_name() == "const-string":
                strs.add(ins.get_output())
    print(f"{cls} extends {cc.get_superclassname()} ifaces={[i for i in cc.get_interfaces()]} strings={sorted(strs)[:6]} nmethods={len(list(cc.get_methods()))}")

print("\n== 5. Lch1;.<init>(I I [Object; Lzv;)V + .j body head + .b(I)I ==")
dump("Lch1;", "<init>", 0, 60)
dump("Lch1;", "j", 0, 40)
dump("Lch1;", "b", 0, 60)

print("\n== 6. Lgi0;-><init>(I)V invoke-direct sites with const tag ==")
for c, m in iter_methods():
    code = m.get_code()
    if code is None: continue
    idx = 0; prev_const = None
    for ins in code.get_bc().get_instructions():
        o = ins.get_output()
        if ins.get_name() in ("const/4", "const/16", "const") :
            prev_const = (idx, o)
        if ins.get_name().startswith("invoke") and "Lgi0;-><init>(I)" in o:
            print(f"  {c.get_name()}->{m.get_name()}{m.get_descriptor()} pc={idx}: {o} | last const: {prev_const}")
        idx += ins.get_length()

print("\n== 7. Lmc0;.E writer Ld8;.d body + Ld8; callers of interest ==")
dump("Ld8;", "d", 370, 400)
for c, m in iter_methods():
    code = m.get_code()
    if code is None: continue
    idx = 0
    for ins in code.get_bc().get_instructions():
        o = ins.get_output()
        if ins.get_name().startswith("invoke") and "Ld8;->d(" in o:
            print(f"  Ld8.d-caller {c.get_name()}->{m.get_name()}{m.get_descriptor()} pc={idx}: {o}")
        idx += ins.get_length()

print("\n== 8. Laj0;.<init>(Lmc0;)V + Ly9;.<init>(I)V heads ==")
dump("Laj0;", "<init>", 0, 80)
dump("Ly9;", "<init>", 0, 90, nth=0)

print("\n== 9. Lx30;.c0(Lpm0;)V head ==")
dump("Lx30;", "c0", 0, 60)
