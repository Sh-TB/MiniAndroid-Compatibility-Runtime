#!/usr/bin/env python3
"""W9: disassemble the chess Toolbar/x0 NPE chain classes at 511b."""
from androguard.misc import AnalyzeDex
import zipfile, io, sys, tempfile, os

APK = '/home/z/my-project/upload/chess_jwtc_298.apk'
WANT = [
    ('Lx0/f;', 'r'),
    ('Lx0/g;', 'r'),
    ('Ll/w;', 'd'),
    ('Ll/w;', 'b'),
    ('Ll/a1;', '<init>'),
    ('Ll/e3;', 'b'),
    ('Landroidx/appcompat/widget/Toolbar;', 'setSubtitle'),
]

# extract all dex files
tmp = tempfile.mkdtemp()
dexes = []
with zipfile.ZipFile(APK) as z:
    for n in z.namelist():
        if n.endswith('.dex'):
            p = os.path.join(tmp, n.replace('/', '_'))
            with open(p, 'wb') as f:
                f.write(z.read(n))
            dexes.append(p)
print(f'{len(dexes)} dex files extracted')

a, d, dx = AnalyzeDex(dexes[0])
d_list = [d]

for cls, meth in WANT:
    found = False
    for d in d_list:
        for c in d.get_classes():
            if c.get_name() != cls:
                continue
            for m in c.get_methods():
                if m.get_name() != meth:
                    continue
                found = True
                print(f'\n===== {cls}->' + meth + ' =====')
                print(f'access: {m.get_access_flags_string()}  proto: {m.get_descriptor()}')
                code = m.get_code()
                if code is None:
                    print('  (abstract/native)')
                    continue
                idx = 0
                for ins in m.get_instructions():
                    op = ins.get_name()
                    out = ins.get_output()
                    print(f'  {idx:4x}: {op:22s} {out[:90]}')
                    idx += ins.get_length()
                    if idx > 0x300:
                        break
    if not found:
        print(f'\n===== {cls}->{meth}: NOT FOUND =====')
