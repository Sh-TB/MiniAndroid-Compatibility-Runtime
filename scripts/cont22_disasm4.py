#!/usr/bin/env python3
"""CONT-22 — F-274 producer trace: Lgf1;.<init> (who should set g), Lg8;.a pc=460
(the consumer), and all writers of Lgf1;->g anywhere in the APK."""
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

def dump_method(c, mname, maxins=200):
    for m in c.get_methods():
        if m.get_name() == mname:
            code = m.get_code()
            if code is None:
                print(f"  METHOD {m.get_name()}{m.get_descriptor()} (no code)")
                return
            print(f"  METHOD {m.get_name()}{m.get_descriptor()}")
            off = 0
            for i, ins in enumerate(m.get_instructions()):
                if i >= maxins:
                    print(f"    ... ({maxins}+ ins)")
                    break
                print(f"    {off:5d}: {ins.get_name():26s} {ins.get_output()[:90]}")
                off += ins.get_length()
            return
    print(f"  no method named {mname}")

cls = {}
for c in classes_from(APK):
    if c.get_name() in ("Lgf1;", "Lg8;"):
        cls[c.get_name()] = c
    if len(cls) == 2:
        break

print("=" * 100)
print("DOOZ Lgf1; — full class")
if "Lgf1;" in cls:
    c = cls["Lgf1;"]
    for f in c.get_fields():
        print(f"  FIELD {f.get_name()} : {f.get_descriptor()}")
    for m in c.get_methods():
        print(f"  HAS-METHOD {m.get_name()}{m.get_descriptor()}")

print("=" * 100)
print("DOOZ Lgf1;.<init> body")
if "Lgf1;" in cls:
    dump_method(cls["Lgf1;"], "<init>")

print("=" * 100)
print("DOOZ Lg8;.a — around offset 460 (consumer)")
if "Lg8;" in cls:
    c = cls["Lg8;"]
    for m in c.get_methods():
        if m.get_name() == "a":
            code = m.get_code()
            if code is None:
                continue
            print(f"  METHOD a{m.get_descriptor()}")
            off = 0
            rows = []
            for ins in m.get_instructions():
                rows.append((off, ins.get_name(), ins.get_output()))
                off += ins.get_length()
            for o, op, out in rows:
                if 400 <= o <= 560:
                    print(f"    {o:5d}: {op:26s} {out[:88]}")
            break

print("=" * 100)
print("DOOZ Lgf1;.c() body (the .g getter)")
if "Lgf1;" in cls:
    dump_method(cls["Lgf1;"], "c")

print("=" * 100)
print("DOOZ Lrf1;.<init>(Lsf1; Lg8;) body")
for c in classes_from(APK):
    if c.get_name() == "Lrf1;":
        dump_method(c, "<init>")
        break

print("=" * 100)
print("DOOZ Lwg0;.<init>(Lrf1; I) body")
c2 = None
for c in classes_from(APK):
    if c.get_name() == "Lwg0;":
        c2 = c
        break
if c2:
    for m in c2.get_methods():
        if m.get_name() == "<init>" and "I" in m.get_descriptor():
            code = m.get_code()
            if code is None:
                print("  (no code)")
                continue
            print(f"  METHOD <init>{m.get_descriptor()}")
            off = 0
            for ins in m.get_instructions():
                print(f"    {off:5d}: {ins.get_name():26s} {ins.get_output()[:90]}")
                off += ins.get_length()
