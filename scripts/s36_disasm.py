#!/usr/bin/env python3
"""S36: full disassembly of named methods in a named class (androguard 4.x)."""
import logging, zipfile, sys
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk'


def disasm(cls, meths):
    z = zipfile.ZipFile(APK)
    d = DEX(z.read('classes.dex'))
    for c in d.get_classes():
        if c.get_name() != cls:
            continue
        for m in c.get_methods():
            if m.get_name() not in meths:
                continue
            print(f"=== {cls}.{m.get_name()} {m.get_descriptor()} ===")
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


if __name__ == '__main__':
    cls = sys.argv[1]
    disasm(cls, set(sys.argv[2:]))
