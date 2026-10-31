#!/usr/bin/env python3
"""cont11_train7_findfilter.py — find all classes with an onPointerEvent method
(the PointerInputModifierNode dispatch target) in the dooz APK.
Also reports SuspendingPointerInputFilter-shaped classes (ctor with
PointerInputEventHandler).
"""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location(
    'cd', '/home/z/my-project/scripts/cont9_dexdump.py')
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)

apk = sys.argv[1] if len(sys.argv) > 1 else \
    '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
target = sys.argv[2] if len(sys.argv) > 2 else 'onPointerEvent'

z = zipfile.ZipFile(apk)
for name in z.namelist():
    if not (name.startswith('classes') and name.endswith('.dex')):
        continue
    d = cd.Dex(z.read(name))
    for i in range(d.class_defs_size):
        off = d.class_defs_off + i * 32
        cls = d.type_str(d.u(off, 4))
        info = d.class_methods(off)
        hits = []
        for kind in ('direct', 'virtual'):
            for mname, mdesc, acc, sz, code in info[kind]:
                if mname == target or (target.startswith("ctor:") and mname == "<init>" and target[5:] in mdesc):
                    codesz = d.u(code + 12, 4) if code else 0
                    hits.append(f'{kind} {mname}{mdesc} insns={codesz}')
        if hits:
            sup = d.type_str(d.u(off + 4, 4))
            print(f'{cls} super={sup}')
            for h in hits:
                print(f'    {h}')
