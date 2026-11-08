#!/usr/bin/env python3
"""S188-W18b: Constants.<clinit> LANGUAGES storage face."""
import zipfile
from androguard.core.dex import DEX

apk = '/home/z/my-project/upload/stuck_apks/se.tube42.p9.android.apk'
z = zipfile.ZipFile(apk)
d = DEX(z.read('classes.dex'))

for cls in d.get_classes():
    cn = cls.get_name() or ''
    if cn != 'Lse/tube42/p9/data/Constants;':
        continue
    for f in cls.get_fields():
        if 'LANGUAGES' in (f.get_name() or ''):
            print('field:', f.get_name(), f.get_descriptor(),
                  f.get_access_flags_string())
    for m in cls.get_methods():
        if (m.get_name() or '') != '<clinit>':
            continue
        print('=== <clinit>', m.get_descriptor())
        pc = 0
        for ins in m.get_code().get_bc().get_instructions():
            out = str(ins.get_output())
            if 'LANGUAGES' in out or 'new-array' in ins.get_name() or \
               'fill-operands' in out or 'array-data' in ins.get_name() or \
               ins.get_name().startswith('sput'):
                print(f'  pc={pc:4d} {ins.get_name():22s} {out[:110]}')
            pc += ins.get_length()
