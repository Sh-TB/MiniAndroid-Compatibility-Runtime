#!/usr/bin/env python3
"""cont35_dump_classes.py — dump class shapes (fields/methods/supertypes) for
the composeStopwatch font-resolution chain around Lk6;.<init> pc=409.
usage: python3.13 cont35_dump_classes.py <apk> <desc1,desc2,...>
"""
import sys, zipfile, io
from androguard.core.dex import DEX

def main():
    apk, descs = sys.argv[1], sys.argv[2].split(",")
    raw = open(apk, "rb").read()
    zf = zipfile.ZipFile(io.BytesIO(raw))
    dexes = [DEX(zf.read(n)) for n in zf.namelist() if n.endswith(".dex")]
    want = set(descs)
    seen = set()
    for d in dexes:
        for c in d.get_classes():
            name = c.get_name()
            if name not in want or name in seen:
                continue
            seen.add(name)
            print(f"== {name}  access={hex(c.get_access_flags())}")
            sname = c.get_superclassname()
            print(f"   extends {sname}")
            ifaces = c.get_interfaces()
            if ifaces:
                print(f"   implements {list(ifaces)}")
            for f in c.get_fields():
                print(f"   field {f.get_name()} : {f.get_descriptor()}")
            for m in c.get_methods():
                code = m.get_code()
                sz = code.get_insns_size() if code else -1
                print(f"   method {m.get_name()}{m.get_descriptor()}  insns={sz}")
    missing = want - seen
    for m in sorted(missing):
        print(f"MISSING: {m}")

if __name__ == "__main__":
    main()
