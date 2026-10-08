#!/usr/bin/env python3
"""CONT-22 — Phase D source-first DEX law disassembly for F-NEW-275 (getServiceInfo
/ PackageInfo.services) and F-NEW-274 (dooz Lwg0;.y savedstate chain).

Prints the exact bytecode around the first-divergence sites so the semantic
law comes from the LIVE APP DEX, not from guessing.
"""
import sys, zipfile, io
from androguard.misc import AnalyzeDex
from androguard.core.bytecodes.dvm import DalvikVMFormat

JOBS = [
    # (label, apk, class, method, show_before, show_after)
    ("opencalc Lg/t;.b (ServiceInfo.metaData face pc=36)",
     "/home/z/my-project/upload/opencalculator_53.apk",
     "Lg/t;", "b", 36, 14, 10),
    ("telegram Lkg/i;.P (getServiceInfo REC-MISS)",
     "/home/z/my-project/upload/telegram_official.apk",
     "Lkg/i;", "P", None, 10, 14),
    ("dooz Lwg0;.y (F-274 face pc=17)",
     "/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apk",
     "Lwg0;", "y", 17, 16, 10),
    ("dooz Lwg0;.z (producer of the provider map)",
     "/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apk",
     "Lwg0;", "z", None, 30, 6),
]

def load_dex(apk):
    z = zipfile.ZipFile(apk)
    names = [n for n in z.namelist() if n.startswith("classes") and n.endswith(".dex")]
    for n in sorted(names):
        data = z.read(n)
        try:
            d = DalvikVMFormat(data)
        except Exception:
            continue
        for c in d.get_classes():
            if c.get_name() == TARGET_CLASS:
                return d, c
    return None, None

TARGET_CLASS = None
TARGET_METHOD = None

def main():
    for label, apk, cls, meth, pc, before, after in JOBS:
        print("=" * 100)
        print("JOB:", label)
        globals()["TARGET_CLASS"] = cls
        found = None
        z = zipfile.ZipFile(apk)
        names = [n for n in z.namelist() if n.startswith("classes") and n.endswith(".dex")]
        for n in sorted(names):
            data = z.read(n)
            try:
                d = DalvikVMFormat(data)
            except Exception:
                continue
            for c in d.get_classes():
                if c.get_name() == cls:
                    found = (d, c)
                    break
            if found:
                break
        if not found:
            print("  CLASS NOT FOUND", cls)
            continue
        d, c = found
        for m in c.get_methods():
            if m.get_name() == meth:
                code = m.get_code()
                if code is None:
                    print("  method", meth, "abstract/native")
                    continue
                bc = m.get_instructions()
                idx = 0
                lines = []
                for ins in bc:
                    op = ins.get_name()
                    out = ins.get_output()
                    lines.append((idx, ins.get_length(), op, out))
                    idx += ins.get_length()
                print(f"  method {cls}.{meth}{m.get_descriptor()}  "
                      f"(units={m.get_code().get_length()})")
                shown = 0
                for i, (off, ln, op, out) in enumerate(lines):
                    hit = (pc is not None and off == pc)
                    near = (pc is not None and abs(off - pc) <= after and off >= pc - before)
                    if pc is None:
                        if shown < before + after:
                            mark = "  "
                            print(f"  {mark}{off:5d}: {op:28s} {out[:90]}")
                            shown += 1
                    elif near or hit:
                        mark = ">>" if hit else "  "
                        print(f"  {mark}{off:5d}: {op:28s} {out[:90]}")
                print()
                break

if __name__ == "__main__":
    main()
