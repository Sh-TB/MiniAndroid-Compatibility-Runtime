#!/usr/bin/env python3
"""S41 Attack-1b: dump full bytecode of specific methods in dooz_23 APK."""
import zipfile, sys
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
d = DEX(z.read('classes.dex'))

# spec = Class:method1,method2 (regex-ish exact match)
for spec in sys.argv[1:]:
    cls_name, meth_names = spec.split(':', 1)
    meth_set = set(meth_names.split(','))
    for c in d.get_classes():
        if c.get_name() != cls_name:
            continue
        for m in c.get_methods():
            if m.get_name() not in meth_set:
                continue
            print(f"=== {cls_name}.{m.get_name()} {m.get_descriptor()} ===")
            code = m.get_code()
            if code is None:
                print('  (no code)')
                continue
            idx = 0
            for ins in code.get_bc().get_instructions():
                try:
                    out = ins.get_output()
                except Exception as e:
                    out = f'<{e}>'
                print(f'  {idx:04x}: {ins.get_name()} {out}')
                idx += ins.get_length()
            print()
