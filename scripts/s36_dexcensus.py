#!/usr/bin/env python3
"""S36: census of dooz DEX — find obfuscated NavControllerImpl (class c) and
the lifecycle chain classes. Writes a census file and prints candidates."""
import logging, zipfile, sys
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk'


def main():
    z = zipfile.ZipFile(APK)
    d = DEX(z.read('classes.dex'))
    classes = d.get_classes()
    print('total classes:', len(classes))
    # sample of short names
    for c in classes[:20]:
        print('sample:', repr(c.get_name()))
    # find androidx.navigation classes that are NOT obfuscated (library ships unobfuscated sometimes)
    nav = [c for c in classes if 'navigation' in c.get_name()]
    print('androidx.navigation classes:', len(nav))
    for c in nav[:40]:
        ms = [m.get_name() for m in c.get_methods()]
        print('  ', c.get_name(), '->', len(ms), 'methods')


if __name__ == '__main__':
    main()
