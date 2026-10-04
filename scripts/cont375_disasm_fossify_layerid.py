#!/usr/bin/env python3
"""cont375 — disassemble Lx4/k;.d (findDrawableByLayerId consumer) in
org.fossify.clock_10.apk: identify the drawable + expected layer id."""
import logging, zipfile
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = '/home/z/my-project/tmp/diff366_apks/org.fossify.clock_10.apk'
TARGET = 'Lx4/k;'
METHODS = ('d', 'b', 'c')

def main():
    z = zipfile.ZipFile(APK)
    for dn in [n for n in z.namelist() if n.endswith('.dex')]:
        raw = z.read(dn)
        if b'Lx4/k;' not in raw:
            continue
        d = DalvikVMFormat(raw)
        for c in d.get_classes():
            if c.get_name() != TARGET:
                continue
            print(f"### class {TARGET} extends {c.get_superclassname()}")
            for m in c.get_methods():
                if m.get_name() not in METHODS:
                    continue
                code = m.get_code()
                if code is None:
                    continue
                print(f"\n### method {m.get_name()} {m.get_descriptor()}")
                idx = 0
                for ins in code.get_bc().get_instructions():
                    print(f"  pc={idx:5d} {ins.get_name():34s} {ins.get_output()[:90]}")
                    idx += ins.get_length()

if __name__ == '__main__':
    main()
