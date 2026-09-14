#!/usr/bin/env python3
"""S36: map Landroidx/navigation/c; (obfuscated NavControllerImpl) methods —
names, sizes, call/xref fingerprints (tryEmit, State, addCallback)."""
import logging, zipfile, sys
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk'


def dump(cls_name):
    z = zipfile.ZipFile(APK)
    d = DEX(z.read('classes.dex'))
    for c in d.get_classes():
        if c.get_name() != cls_name:
            continue
        try:
            sup = d.get_string(c.get_superclass_idx())
        except Exception:
            sup = '?'
        print(f"=== {cls_name} extends {sup} ===")
        for f in c.get_fields():
            print(f"  FIELD {f.get_name()} : {f.get_descriptor()}")
        for m in c.get_methods():
            code = m.get_code()
            size = code.get_length() if code else 0
            print(f"  METH {m.get_name()} {m.get_descriptor()}  [{size} units]")


if __name__ == '__main__':
    for cls in sys.argv[1:]:
        dump(cls)
