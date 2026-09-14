#!/usr/bin/env python3
"""S36: xref — find every instruction in the DEX touching a given field
(read iget* / write iput*), with the enclosing class.method."""
import logging, zipfile, sys
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk'


def xref(field_sig):
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
                try:
                    out = ins.get_output()
                except Exception:
                    out = ''
                if field_sig in out and ('iput' in name or 'iget' in name or 'sput' in name or 'sget' in name):
                    kind = ('WRITE' if ('iput' in name or 'sput' in name) else 'READ')
                    hits.append((cn, m.get_name(), m.get_descriptor(), f'{idx:04x}', name, out.strip(), kind))
                idx += ins.get_length()
    for h in hits:
        print(f'{h[6]:5s} {h[0]}.{h[1]}{h[2]} @ {h[3]}: {h[4]} {h[5]}')
    print(f'-- total {len(hits)} hits for {field_sig}')


if __name__ == '__main__':
    xref(sys.argv[1])
