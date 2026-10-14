#!/usr/bin/env python3
"""CONT-43: decode csw Lh4;.onMeasure pc=78/167 + Laj0;.n + Li01; (ReportFragment).
Field-ref-exact androguard disasm of the F-NEW-304 regression site."""
import zipfile
from androguard.core.dex import DEX

APK = '/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk'
z = zipfile.ZipFile(APK)
dexas = [DEX(z.read(n)) for n in z.namelist() if n.endswith('.dex')]

def find_method(cls, name):
    for d in dexas:
        for c in d.get_classes():
            if c.get_name() == cls:
                for m in c.get_methods():
                    if m.get_name() == name:
                        return m
    return None

def dump(cls, name, pcs=None):
    m = find_method(cls, name)
    if m is None:
        print(f"== {cls}->{name}: NOT FOUND")
        return
    print(f"== {m.get_class_name()}->{m.get_name()}{m.get_descriptor()}")
    code = m.get_code()
    if code is None:
        print("  (no code)")
        return
    idx = 0
    for ins in code.get_bc().get_instructions():
        if pcs is None or idx in pcs:
            print(f"  pc={idx}: {ins.get_name()} {ins.get_output()}")
        idx += ins.get_length()

# superclass identity
for d in dexas:
    for c in d.get_classes():
        if c.get_name() in ("Lh4;", "Laj0;", "Li01;"):
            print(f"class {c.get_name()} extends {c.get_superclassname()}")

print()
dump("Lh4;", "onMeasure", pcs=set(range(70, 90)) | set(range(160, 172)))
print()
dump("Laj0;", "n")

print("\n=== Ly9; / Lgi0; fields + Lgi0;.f writers ===")
for d in dexas:
    for c in d.get_classes():
        if c.get_name() in ("Ly9;", "Lgi0;"):
            print(f"class {c.get_name()} extends {c.get_superclassname()}")
            for f in c.get_fields():
                print(f"  field {f.get_name()} : {f.get_descriptor()}")
            for m in c.get_methods():
                code = m.get_code()
                if code is None: continue
                idx = 0; hits = []
                for ins in code.get_bc().get_instructions():
                    op = ins.get_name()
                    if ("iput" in op and "Lgi0;->f" in ins.get_output()) or \
                       ("iput" in op and c.get_name()=="Ly9;" and "->c " in ins.get_output()):
                        hits.append(f"    {m.get_name()}{m.get_descriptor()} pc={idx}: {op} {ins.get_output()}")
                    idx += ins.get_length()
                for h in hits[:4]: print(h)
