#!/usr/bin/env python3
"""cont11_train7_fieldscan.py — find methods that WRITE (iput-wide) a given field,
and methods that READ it. Usage: cont11_train7_fieldscan.py <Lcls;> <field> [apk]
"""
import sys, zipfile, importlib.util, types

spec = importlib.util.spec_from_file_location(
    'cd', '/home/z/my-project/scripts/cont9_dexdump.py')
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)

src = open('/home/z/my-project/scripts/cont11_decode.py').read()
mod = types.ModuleType('c11')
exec(compile(src.split('def main()')[0], 'cont11_tables', 'exec'), mod.__dict__)
W, NAMES = mod.W, mod.NAMES

cls = sys.argv[1]
field = sys.argv[2]
apk = sys.argv[3] if len(sys.argv) > 3 else \
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
        info = d.class_methods(off)
        for kind in ('direct', 'virtual'):
            for mname, mdesc, acc, sz, code in info[kind]:
                if not code:
                    continue
                insns_size = d.u(code + 12, 4)
                base = code + 16
                words = [d.u(base + 2 * w, 2) for w in range(insns_size)]
                w = 0
                puts, gets = [], []
                while w < insns_size:
                    wd = words[w]
                    op = wd & 0xff
                    u, f = W.get(op, (1, '?'))
                    if op in (0x59, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f, 0x60,
                              0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68,
                              0x69, 0x6a):
                        if w + 1 < insns_size:
                            fidx = words[w + 1]
                            try:
                                c2, n2, t2 = d.field_ref(fidx)
                                if c2 == cls and n2 == field:
                                    tag = 'PUT' if 0x59 <= op <= 0x6a and op in (0x59, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f) else 'GET'
                                    (puts if tag == 'PUT' else gets).append(w)
                            except Exception:
                                pass
                    w += u
                if puts or gets:
                    print(f'{mname}{mdesc} insns={insns_size} PUTs={puts} GETs={gets[:12]}')
        sys.exit(0)
print(f'class {cls} not found')
