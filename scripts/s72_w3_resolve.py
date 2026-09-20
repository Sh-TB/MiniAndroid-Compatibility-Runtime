#!/usr/bin/env python3
"""Resolve dooz DEX indices seen at the f141 NPE sites: methods 6923, 6624,
6916, 7409, 10134, 6789, 7046, 6914; class 3362; fields 9789, 9762, 9790;
strings 9422, 9430."""
import zipfile
try:
    from androguard.core.bytecodes.dvm import DalvikVMFormat as DEX
except ImportError:
    from androguard.core.dex import DEX

APK = "/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apk"
METHODS = {6923, 6624, 6916, 7409, 10134, 6789, 7046, 6914}
CLASSES = {3362}
FIELDS = {9789, 9762, 9790}
STRINGS = {9422, 9430}

with zipfile.ZipFile(APK) as z:
    dex_data = {n: z.read(n) for n in z.namelist() if n.endswith(".dex")}

for dname, raw in dex_data.items():
    d = DEX(raw)
    cm = d.get_class_manager() if hasattr(d, "get_class_manager") else None
    print(f"--- {dname} ---")
    for mid in sorted(METHODS):
        try:
            s = cm.get_method_ref(mid) if cm else d.get_method(mid)
            print(f"  method[{mid}] = {s.get_class_name()}->{s.get_name()}{s.get_descriptor()}")
        except Exception as e:
            print(f"  method[{mid}] = <err {e}>")
    for cid in sorted(CLASSES):
        try:
            print(f"  class[{cid}] = {cm.get_class_ref(cid) if cm else d.get_class(cid)}")
        except Exception as e:
            print(f"  class[{cid}] = <err {e}>")
    for fid in sorted(FIELDS):
        try:
            s = cm.get_field_ref(fid) if cm else d.get_field(fid)
            print(f"  field[{fid}] = {s.get_class_name()}.{s.get_name()}:{s.get_descriptor()}")
        except Exception as e:
            print(f"  field[{fid}] = <err {e}>")
    for sid in sorted(STRINGS):
        try:
            print(f"  string[{sid}] = {cm.get_string(sid) if cm else d.get_string(sid)!r}")
        except Exception as e:
            print(f"  string[{sid}] = <err {e}>")
