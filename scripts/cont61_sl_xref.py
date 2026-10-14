#!/usr/bin/env python3
"""cont61_sl_xref.py — W1 (CONT-61): who calls Landroid/text/StaticLayout;
across every classes*.dex? Reuses the cont9_dexdump Dex parser.

Usage: cont61_sl_xref.py <apk> [target-ldesc-substr] [method-substr]
Prints: caller_class -> caller_method(signature) : invoked-line
"""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location(
    "c9", "/home/z/my-project/scripts/cont9_dexdump.py")
c9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c9)

def scan(apk, target="StaticLayout;", method=None):
    z = zipfile.ZipFile(apk)
    dexnames = sorted(n for n in z.namelist()
                      if n.startswith("classes") and n.endswith(".dex"))
    hits = 0
    for dn in dexnames:
        d = c9.Dex(z.read(dn))
        for ci in range(d.class_defs_size):
            off = d.class_defs_off + ci * 32
            cls = d.type_str(d.u(off, 4))
            try:
                cm = d.class_methods(off)
            except Exception:
                continue
            for kind in ("direct", "virtual"):
                for (mname, mdesc, acc, sz, code) in cm[kind]:
                    if not code:
                        continue
                    try:
                        code_lines = d.disasm(code)
                    except Exception:
                        continue
                    for line in code_lines:
                        if target in line and "invoke" in line:
                            if method and method not in line:
                                continue
                            print("%s -> %s%s : %s" % (cls, mname, mdesc,
                                                       line.strip()))
                            hits += 1
    print("TOTAL", hits)

if __name__ == "__main__":
    apk = sys.argv[1]
    tgt = sys.argv[2] if len(sys.argv) > 2 else "StaticLayout;"
    meth = sys.argv[3] if len(sys.argv) > 3 else None
    scan(apk, tgt, meth)
