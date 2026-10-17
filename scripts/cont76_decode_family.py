#!/usr/bin/env python3
"""CONT-76: identify La; (CancellationException family), Ltb1;/Lt81; holders,
Lxv0.c (suspension point), Lgt;/Lys; (ContinuationImpl) + La; constructor bodies."""
import logging
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
import zipfile
from androguard.core.dex import DEX

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
WANT = {"La;", "Ltb1;", "Lt81;", "Lxv0;", "Lgt;", "Lys;", "Llo;", "Lwr;"}


def dump_method(m):
    code = m.get_code()
    if code is None:
        print("        <no code>")
        return
    off = 0
    for ins in code.get_bc().get_instructions():
        try:
            ln = ins.get_length()
        except Exception:
            ln = 2
        try:
            print(f"        {off:04x}: {ins.get_name():22s} {ins.get_output()}")
        except Exception:
            pass
        off += ln


def main():
    z = zipfile.ZipFile(APK)
    for dname in [n for n in z.namelist()
                  if n.startswith("classes") and n.endswith(".dex")]:
        d = DEX(z.read(dname))
        for c in d.get_classes():
            try:
                cn = c.get_name()
            except Exception:
                continue
            if cn not in WANT:
                continue
            print("=" * 92)
            print(f"CLASS {cn} extends {c.get_superclassname()}"
                  f" ifc={list(c.get_interfaces())}")
            for f in c.get_fields():
                print(f"  field {f.get_name()} : {f.get_descriptor()}")
            for m in c.get_methods():
                print(f"  method {m.get_name()} {m.get_descriptor()}")
                dump_method(m)


if __name__ == "__main__":
    main()
