#!/usr/bin/env python3
"""S41 Attack-1: disassemble R-NEW-344 obfuscated classes from dooz_23 APK.
Targets: Loj0; (.Q await path), Lkp1; (job subclass), Lh9; (frame callback),
Lrx; (resume runnable), Lcj; (CancellableContinuationImpl), Ley; (COROUTINE_SUSPENDED holder)
"""
import zipfile, sys, json
import logging
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/s36new/io.github.yamin8000.dooz_23.apk'

z = zipfile.ZipFile(APK)
dex_names = [n for n in z.namelist() if n.endswith('.dex')]
print("DEX files:", dex_names)

classes = {}
for dn in dex_names:
    d = DEX(z.read(dn))
    for c in d.get_classes():
        name = c.get_name()
        if name in classes:
            continue
        classes[name] = (dn, c)

targets = sys.argv[1:] if len(sys.argv) > 1 else ['Loj0;', 'Lkp1;', 'Lh9;', 'Lrx;', 'Lcj;', 'Ley;']

for t in targets:
    if t not in classes:
        print(f"### {t}: NOT FOUND")
        continue
    dn, c = classes[t]
    print(f"\n### {t} (in {dn}) super={c.get_superclassname()}")
    ifaces = c.get_interfaces()
    if ifaces:
        print(f"    interfaces={ifaces}")
    # field list
    for f in c.get_fields():
        print(f"    FIELD {f.get_name()} {f.get_descriptor()}")
    for m in c.get_methods():
        print(f"    METHOD {m.get_name()} {m.get_descriptor()} "
              f"access={m.get_access_flags_string()}")
