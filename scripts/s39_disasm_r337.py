#!/usr/bin/env python3
"""S39: disassemble Loj0;.T (JobSupport.makeCompletingOnce) + Lh20; (Empty)
+ Lkp1; class header from dooz_23 APK. Decisive for R-NEW-337: which
instance-of/cast does pc<=49 execute, and does Lh20; implement Incomplete?"""
import logging, zipfile, sys
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/s36new/io.github.yamin8000.dooz_23.apk'

TARGET_CLASSES = ['Loj0;', 'Lh20;', 'Lkp1;', 'Lwl;']
DISASM_METHODS = {'Loj0;': ['T']}


def main():
    z = zipfile.ZipFile(APK)
    # find all dex files, search each
    dexnames = [n for n in z.namelist() if n.endswith('.dex')]
    print(f"dex files: {dexnames}")
    for dn in dexnames:
        d = DEX(z.read(dn))
        for c in d.get_classes():
            name = c.get_name()
            if name not in TARGET_CLASSES:
                continue
            sname = c.get_superclassname()
            ifaces = list(c.get_interfaces() or [])
            print(f"\n### class {name} extends {sname} implements {ifaces} (in {dn})")
            for m in c.get_methods():
                mn = m.get_name()
                if name in DISASM_METHODS and mn in DISASM_METHODS[name]:
                    print(f"=== {name}.{mn} {m.get_descriptor()} ===")
                    code = m.get_code()
                    if code is None:
                        print('  (no code)')
                        continue
                    idx = 0
                    for ins in code.get_bc().get_instructions():
                        op = ins.get_name()
                        out = ins.get_output()
                        print(f"  {idx:4d}: {op} {out}")
                        idx += ins.get_length()
                    print(f"  (total {idx} code units)")
                # fields
            for f in c.get_fields():
                print(f"  field: {f.get_name()} : {f.get_descriptor()}")


if __name__ == '__main__':
    main()
