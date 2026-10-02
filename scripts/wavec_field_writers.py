#!/usr/bin/env python3
"""F-NEW-169: find every READ/WRITE site of a given field across all dexes.
Usage: wavec_field_writers.py "<class-desc>" "<field-name>"
"""
import logging, sys, zipfile
logging.disable(logging.CRITICAL)
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = '/tmp/my-project/apk_cache/WhatsApp_real.apk'
CLS = sys.argv[1]          # e.g. LX/0IH;
FLD = sys.argv[2]          # e.g. A0B

z = zipfile.ZipFile(APK)
dexes = sorted(n for n in z.namelist()
               if n.startswith('classes') and n.endswith('.dex'))
for dname in dexes:
    try:
        d = DalvikVMFormat(z.read(dname))
    except Exception:
        continue
    for c in d.get_classes():
        for m in c.get_methods():
            code = m.get_code()
            if code is None:
                continue
            for ins in code.get_bc().get_instructions():
                try:
                    op = ins.get_name()
                    if op in ('iput-object', 'iput', 'sput-object', 'sput',
                              'iget-object', 'sget-object'):
                        out = ins.get_output()
                        if FLD + ' ' in out and CLS in out:
                            print(f'[{dname}] {c.get_name()}.{m.get_name()}'
                                  f' {op} {out[:100]}')
                except Exception:
                    pass
