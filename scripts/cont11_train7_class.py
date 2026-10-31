#!/usr/bin/env python3
"""cont11_train7_class.py — dump a class's method list (name, proto, access, code size)
from the dooz APK. Usage: cont11_train7_class.py <Lcls;> [apk]
"""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location(
    'cd', '/home/z/my-project/scripts/cont9_dexdump.py')
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)

cls = sys.argv[1]
apk = sys.argv[2] if len(sys.argv) > 2 else \
    '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'

z = zipfile.ZipFile(apk)
for name in z.namelist():
    if not (name.startswith('classes') and name.endswith('.dex')):
        continue
    d = cd.Dex(z.read(name))
    for i in range(d.class_defs_size):
        off = d.class_defs_off + i * 32
        if d.type_str(d.u(off, 4)) != cls:
            continue
        # superclass
        sup_idx = d.u(off + 4, 4)
        print(f'class {cls} dex={name} super={d.type_str(sup_idx)}')
        info = d.class_methods(off)
        for kind in ('direct', 'virtual'):
            for mname, mdesc, acc, sz, code in info[kind]:
                codesz = d.u(code + 12, 4) if code else 0
                print(f'  {kind:8s} {mname}{mdesc} acc={acc:#06x} insns={codesz}')
        sys.exit(0)
print(f'NOT FOUND {cls}')
