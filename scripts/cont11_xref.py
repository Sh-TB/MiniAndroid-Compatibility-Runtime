#!/usr/bin/env python3
"""cont11_xref.py — cross-reference scanner for dooz APK (CONT-11 W7).

Finds every class whose code items contain:
  - new-instance of a target class
  - const-string matching a target substring
  - invoke on a target class
Usage: cont11_xref.py <apk> [--new Lcls;] [--str substring] [--call Lcls;]
"""
import sys, importlib.util

spec = importlib.util.spec_from_file_location('cd', '/home/z/my-project/scripts/cont9_dexdump.py')
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)

SFIELD_OPS = {0x13: 2, 0x16: 2, 0x19: 2, 0x14: 4, 0x17: 4, 0x18: 8}


def main():
    apk = sys.argv[1]
    args = sys.argv[2:]
    new_t = args[args.index('--new') + 1] if '--new' in args else None
    str_t = args[args.index('--str') + 1] if '--str' in args else None
    call_t = args[args.index('--call') + 1] if '--call' in args else None

    z = __import__('zipfile').ZipFile(apk)
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
                    if not code:
                        continue
                    body = d.disasm(code)
                    for line in body:
                        if new_t and f'new-instance v{"" if False else ""}' in line and new_t in line:
                            hits.append(f'{kind} {mname}{mdesc}: {line.strip()}')
                        if str_t and str_t in line:
                            hits.append(f'{kind} {mname}{mdesc}: {line.strip()[:150]}')
                        if call_t and (call_t + '->') in line:
                            hits.append(f'{kind} {mname}{mdesc}: {line.strip()[:150]}')
            if hits:
                print(f'== {cls} (super={info["super"]})')
                for h in hits[:8]:
                    print('   ', h)
                if len(hits) > 8:
                    print(f'    ... {len(hits) - 8} more')


if __name__ == '__main__':
    main()
