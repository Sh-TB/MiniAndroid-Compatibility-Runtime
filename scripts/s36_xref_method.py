#!/usr/bin/env python3
"""S36: method-call xref — find every invoke-* targeting given method signatures."""
import logging, zipfile, sys
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk'


def xref(sig):
    z = zipfile.ZipFile(APK)
    d = DEX(z.read('classes.dex'))
    hits = []
    for c in d.get_classes():
        cn = c.get_name()
        for m in c.get_methods():
            code = m.get_code()
            if code is None:
                continue
            idx = 0
            for ins in code.get_bc().get_instructions():
                name = ins.get_name()
                if name.startswith('invoke'):
                    try:
                        out = ins.get_output()
                    except Exception:
                        out = ''
                    if sig in out:
                        hits.append((cn, m.get_name(), f'{idx:04x}', name, out.strip()))
                idx += ins.get_length()
    for h in hits:
        print(f'CALL {h[0]}.{h[1]} @ {h[2]}: {h[3]} {h[4]}')
    print(f'-- {len(hits)} call sites for {sig}')


if __name__ == '__main__':
    for s in sys.argv[1:]:
        xref(s)
        print()
