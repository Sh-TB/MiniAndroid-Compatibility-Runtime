#!/usr/bin/env python3
"""CONT44-A part 2: pin down the exact NPE thrower frames and Lgi0;/Lch1;/Lmc0;
original androidx identities + allocation contract."""
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

def dump(cls, name, desc_prefix=None, lo=0, hi=10**9):
    for c, m in iter_methods():
        if c.get_name() == cls and m.get_name() == name and \
           (desc_prefix is None or m.get_descriptor().startswith(desc_prefix)):
            print(f"-- {cls}->{name}{m.get_descriptor()} [{lo}..{hi}] --")
            for l in disasm(m, lo, hi): print(l)
            return

# strings in class (const-string) to identify original androidx classes
def strings_of(cls):
    c = find_class(cls)
    strs = set()
    if not c: return strs
    for m in c.get_methods():
        code = m.get_code()
        if not code: continue
        for ins in code.get_bc().get_instructions():
            if ins.get_name() == "const-string":
                strs.add(ins.get_output().split('"')[1] if '"' in ins.get_output() else ins.get_output())
    return strs

print("== A. Laj0; class identity ==")
c = find_class("Laj0;")
print(f"Laj0; extends {c.get_superclassname()} ifaces={[i for i in c.get_interfaces()]}")
for f in c.get_fields(): print(f"  field {f.get_name()} : {f.get_descriptor()}")
for m in c.get_methods(): print(f"  method {m.get_name()}{m.get_descriptor()}")

print("\n== B. Laj0;.n(Ld3;Lh4;)Ld3; pc 180..230 (invoke@194/try210/handler212) ==")
dump("Laj0;", "n", "(Ld3;", 180, 230)

print("\n== C. Lmc0; identity + z() + E writers ==")
c = find_class("Lmc0;")
print(f"Lmc0; extends {c.get_superclassname()}")
for f in c.get_fields(): print(f"  field {f.get_name()} : {f.get_descriptor()}")
for cls_name in ("Lmc0;", "Lch1;", "Lg91;", "Ly9;", "Lel;", "Lx30;", "Lku0;", "Lhl;"):
    s = strings_of(cls_name)
    print(f"  strings[{cls_name}] = {sorted(s)[:12]}")
for cc, m in iter_methods():
    code = m.get_code()
    if code is None: continue
    idx = 0
    for ins in code.get_bc().get_instructions():
        if ins.get_name().startswith("iput") and "Lmc0;->E" in ins.get_output():
            print(f"  E-writer {cc.get_name()}->{m.get_name()}{m.get_descriptor()} pc={idx}")
        if ins.get_name().startswith("iput") and "Lch1;->d" in ins.get_output():
            print(f"  ch1.d-writer {cc.get_name()}->{m.get_name()}{m.get_descriptor()} pc={idx}")
        if ins.get_name().startswith("iput") and "Ly9;->c" in ins.get_output():
            print(f"  y9.c-writer {cc.get_name()}->{m.get_name()}{m.get_descriptor()} pc={idx}")
        idx += ins.get_length()

print("\n== D. Lmc0;.z body + Lcj0;.j0 130..160 ==")
dump("Lmc0;", "z")
dump("Lcj0;", "j0", None, 128, 160)

print("\n== E. Lgi0;.g(Lmc0;)V / .o(Lmc0;)Z + their callers ==")
dump("Lgi0;", "g", "(Lmc0;")
dump("Lgi0;", "o", "(Lmc0;")
for cc, m in iter_methods():
    code = m.get_code()
    if code is None: continue
    idx = 0
    for ins in code.get_bc().get_instructions():
        o = ins.get_output()
        if ins.get_name().startswith("invoke") and ("Lgi0;->g(Lmc0;)" in o or "Lgi0;->o(Lmc0;)" in o):
            print(f"  caller {cc.get_name()}->{m.get_name()}{m.get_descriptor()} pc={idx}: {o}")
        idx += ins.get_length()

print("\n== F. who calls Laj0;.n()V and Laj0;.n(Ld3;Lh4;)Ld3; ==")
for cc, m in iter_methods():
    code = m.get_code()
    if code is None: continue
    idx = 0
    for ins in code.get_bc().get_instructions():
        o = ins.get_output()
        if ins.get_name().startswith("invoke") and "Laj0;->n" in o:
            print(f"  caller {cc.get_name()}->{m.get_name()}{m.get_descriptor()} pc={idx}: {o}")
        idx += ins.get_length()

print("\n== G. Lel;.j / Lez0;.a / Lad0;.m / Lx30;.n caller context ==")
dump("Lel;", "j", None, 28, 60)
dump("Lx30;", "n", "(Lpm0;", 60, 100)

print("\n== H. Lch1;.<clinit> and Lch1;.s callers ==")
dump("Lch1;", "<clinit>")
for cc, m in iter_methods():
    code = m.get_code()
    if code is None: continue
    idx = 0
    for ins in code.get_bc().get_instructions():
        o = ins.get_output()
        if ins.get_name().startswith("invoke") and "Lch1;->s" in o:
            print(f"  ch1.s-caller {cc.get_name()}->{m.get_name()}{m.get_descriptor()} pc={idx}: {o}")
        idx += ins.get_length()
