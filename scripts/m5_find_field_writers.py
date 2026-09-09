#!/usr/bin/env python3
"""M5: find DEX methods that write fields of Lh/u; via androguard."""
from loguru import logger
logger.remove()
import zipfile
from androguard.core.dex import DEX

dex_data = zipfile.ZipFile('/home/z/my-project/apk_cache/corpus/dooz.apk').read('classes.dex')
d = DEX(dex_data)

iput_ops = {'iput', 'iput-wide', 'iput-object', 'iput-boolean', 'iput-byte',
            'iput-char', 'iput-short'}
found = 0
for c in d.get_classes():
    for m in c.get_methods():
        code = m.get_code()
        if not code:
            continue
        for ins in code.get_bc().get_instructions():
            name = ins.get_name()
            if name in iput_ops:
                out = ins.get_output()
                if 'Lh/u;' in out:
                    print(f"WRITER {c.get_name()}.{m.get_name()}{m.get_descriptor()}: {name} {out}")
                    found += 1
print(f"total writers: {found}")
