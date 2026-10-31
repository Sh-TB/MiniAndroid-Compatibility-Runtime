#!/usr/bin/env python3
"""cont11_train7_ifaces.py — find classes implementing a given interface (or
whose ctor signature mentions a type). Usage: cont11_train7_ifaces.py <Liface;>
"""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location(
    'cd', '/home/z/my-project/scripts/cont9_dexdump.py')
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)

iface = sys.argv[1]
apk = sys.argv[2] if len(sys.argv) > 2 else \
    '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'

z = zipfile.ZipFile(apk)
for name in z.namelist():
    if not (name.startswith('classes') and name.endswith('.dex')):
        continue
    d = cd.Dex(z.read(name))
    for i in range(d.class_defs_size):
        off = d.class_defs_off + i * 32
        # interfaces_off at offset 28 (class_def: class_idx, access, super,
        # interfaces_off, source_file_off, annotations_off, class_data_off,
        # static_values_off)
        ifaces_off = d.u(off + 12, 4)  # class_def: class_idx@0,access@4,super@8,interfaces@12
        hit = False
        if ifaces_off:
            n = d.u(ifaces_off, 4)
            for k in range(n):
                if d.type_str(d.u(ifaces_off + 4 + k * 2, 2)) == iface:
                    hit = True
                    break
        if hit:
            cls = d.type_str(d.u(off, 4))
            sup = d.type_str(d.u(off + 4, 4))
            print(f'{cls} super={sup}')
            info = d.class_methods(off)
            for kind in ('direct', 'virtual'):
                for mname, mdesc, acc, sz, code in info[kind]:
                    codesz = d.u(code + 12, 4) if code else 0
                    print(f'    {kind:8s} {mname}{mdesc} insns={codesz}')
