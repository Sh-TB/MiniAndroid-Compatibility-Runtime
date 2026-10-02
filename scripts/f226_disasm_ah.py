#!/usr/bin/env python3
"""F-NEW-221 evidence: disassemble LA/h; (R8 horizontal merge host) from opencalc.
Capture: fields, all ctors (mode switch paths), method z, and the call sites.
"""
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


def load_dex_objects(apk_path):
    z = zipfile.ZipFile(apk_path)
    out = []
    for name in z.namelist():
        if name.endswith(".dex"):
            d = DEX(z.read(name))
            out.append((name, d))
    return out


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "LA/h;"
    for name, d in load_dex_objects(APK):
        for m in d.get_classes():
            cname = m.get_name()
            if cname != target:
                continue
            print(f"=== {target} in {name} extends {m.get_superclassname()} ===")
            print("access:", m.get_access_flags_string())
            print("--- FIELDS ---")
            for f in m.get_fields():
                print(f"  {f.get_access_flags_string()} {f.get_descriptor()} {f.get_name()}")
            print("--- METHODS ---")
            for meth in m.get_methods():
                mname = meth.get_name()
                proto = meth.get_descriptor()
                print(f"\n### METHOD {mname}{proto} flags={meth.get_access_flags_string()}")
                code = meth.get_code()
                if code is None:
                    print("  <abstract/native>")
                    continue
                off = 0
                for ins in code.get_bc().get_instructions():
                    op = ins.get_name()
                    out = ins.get_output()
                    try:
                        ln = ins.get_length()
                    except Exception:
                        ln = 2
                    print(f"  {off:6x} {op:26s} {out}")
                    off += ln
                print()


if __name__ == "__main__":
    main()
