#!/usr/bin/env python3
"""CONT-22 — full method dumps: opencalc Lg/t;.b (complete), all dooz Lwg0; methods
with iget Lrf1;->f, and Lrf1; class field table."""
import zipfile
from androguard.core.bytecodes.dvm import DalvikVMFormat

def classes_from(apk):
    z = zipfile.ZipFile(apk)
    for n in sorted(x for x in z.namelist()
                    if x.startswith("classes") and x.endswith(".dex")):
        try:
            d = DalvikVMFormat(z.read(n))
        except Exception:
            continue
        for c in d.get_classes():
            yield c

print("=" * 100)
print("OPENCALC Lg/t;.b — FULL")
for c in classes_from("/home/z/my-project/upload/opencalculator_53.apk"):
    if c.get_name() == "Lg/t;":
        for m in c.get_methods():
            if m.get_name() == "b":
                print(f"  {m.get_name()}{m.get_descriptor()}")
                off = 0
                for ins in m.get_instructions():
                    print(f"    {off:5d}: {ins.get_name():30s} {ins.get_output()[:95]}")
                    off += ins.get_length()
        break

print("=" * 100)
print("DOOZ Lwg0; — all methods containing 'Lrf1;->f'")
for c in classes_from("/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apk"):
    if c.get_name() == "Lwg0;":
        for m in c.get_methods():
            body = []
            off = 0
            hit = False
            for ins in m.get_instructions():
                o = ins.get_output()
                if "Lrf1;->f" in o:
                    hit = True
                body.append((off, ins.get_name(), o))
                off += ins.get_length()
            if hit:
                print(f"  METHOD {m.get_name()}{m.get_descriptor()}")
                for o2, op, out in body:
                    print(f"    {o2:5d}: {op:28s} {out[:95]}")
        break

print("=" * 100)
print("DOOZ Lrf1; — field table + short methods")
for c in classes_from("/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apk"):
    if c.get_name() == "Lrf1;":
        for f in c.get_fields():
            print(f"  FIELD {f.get_name()} : {f.get_descriptor()}")
        for m in c.get_methods():
            off = 0
            n_ins = 0
            for ins in m.get_instructions():
                n_ins += 1
                off += ins.get_length()
            print(f"  METHOD {m.get_name()}{m.get_descriptor()}  code_units={off} ins={n_ins}")
        break
