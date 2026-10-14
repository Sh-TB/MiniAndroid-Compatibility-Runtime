#!/usr/bin/env python3
"""CONT-22 — full Lwg0;.y dump + Lgf1;.g field context + who writes Lrf1; instances."""
import zipfile
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = "/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apk"

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

want = {"Lwg0;", "Lgf1;"}
found = {}
for c in classes_from(APK):
    if c.get_name() in want and c.get_name() not in found:
        found[c.get_name()] = c
    if len(found) == len(want):
        break

c = found.get("Lwg0;")
print("=" * 100)
print("DOOZ Lwg0; — ALL methods, full bodies")
if c:
    for m in c.get_methods():
        code = m.get_code()
        if code is None:
            print(f"  METHOD {m.get_name()}{m.get_descriptor()} (no code)")
            continue
        print(f"  METHOD {m.get_name()}{m.get_descriptor()}")
        off = 0
        for ins in m.get_instructions():
            print(f"    {off:5d}: {ins.get_name():26s} {ins.get_output()[:92]}")
            off += ins.get_length()
else:
    print("  Lwg0; not found")

c = found.get("Lgf1;")
print("=" * 100)
print("DOOZ Lgf1; — fields + g() method")
if c:
    for f in c.get_fields():
        print(f"  FIELD {f.get_name()} : {f.get_descriptor()}")
    for m in c.get_methods():
        if m.get_name() != "g":
            continue
        code = m.get_code()
        if code is None:
            print(f"  METHOD g{m.get_descriptor()} (no code)")
            continue
        print(f"  METHOD g{m.get_descriptor()}")
        off = 0
        for ins in m.get_instructions():
            print(f"    {off:5d}: {ins.get_name():26s} {ins.get_output()[:92]}")
            off += ins.get_length()
