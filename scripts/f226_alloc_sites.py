#!/usr/bin/env python3
"""F-NEW-221 part 2: find LA/h; allocation sites + ctor call sites + Lc1/d;.c body."""
import sys
import logging, zipfile
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = "/home/z/my-project/upload/opencalculator_53.apk"


def disasm_method(meth, max_ins=400):
    code = meth.get_code()
    if code is None:
        print("  <no code>")
        return
    off = 0
    n = 0
    for ins in code.get_bc().get_instructions():
        op = ins.get_name()
        out = ins.get_output()
        try:
            ln = ins.get_length()
        except Exception:
            ln = 2
        print(f"  {off:6x} {op:26s} {out}")
        off += ln
        n += 1
        if n >= max_ins:
            print(f"  ... truncated at {max_ins}")
            break


def main():
    z = zipfile.ZipFile(APK)
    target_caller = sys.argv[1] if len(sys.argv) > 1 else "Lc1/d;"
    target_method = sys.argv[2] if len(sys.argv) > 2 else "c"
    # 1. all new-instance LA/h; + invoke-direct A/h ctors
    print("=== LA/h; ALLOCATION SITES (new-instance + invoke-direct) ===")
    for dn in z.namelist():
        if not dn.endswith(".dex"):
            continue
        d = DEX(z.read(dn))
        for c in d.get_classes():
            for m in c.get_methods():
                code = m.get_code()
                if code is None:
                    continue
                news = []
                offs = 0
                for ins in code.get_bc().get_instructions():
                    op = ins.get_name()
                    out = ins.get_output()
                    if "LA/h;-><init>" in out or (op == "new-instance" and "LA/h;" in out):
                        news.append((offs, op, out))
                    try:
                        offs += ins.get_length()
                    except Exception:
                        offs += 2
                if news:
                    print(f"{c.get_name()}.{m.get_name()}{m.get_descriptor()} [{dn}]:")
                    for o, op, out in news:
                        print(f"    {o:6x} {op:22s} {out}")
    # 2. caller body
    print(f"\n=== {target_caller} methods (body of '{target_method}') ===")
    for dn in z.namelist():
        if not dn.endswith(".dex"):
            continue
        d = DEX(z.read(dn))
        for c in d.get_classes():
            if c.get_name() != target_caller:
                continue
            print(f"--- class {target_caller} extends {c.get_superclassname()} fields:")
            for f in c.get_fields():
                print(f"    {f.get_access_flags_string()} {f.get_descriptor()} {f.get_name()}")
            for m in c.get_methods():
                if m.get_name() != target_method:
                    continue
                print(f"\n### METHOD {m.get_name()}{m.get_descriptor()}")
                disasm_method(m)


if __name__ == "__main__":
    main()
