#!/usr/bin/env python3
"""s141_train41_b.py — TRAIN-41: who calls Luq;.h (the ONLY caller of the
clickable's composed factory body Lpm;.c)? Ref-resolved disasm of Luq;.h +
full caller census. This pins the exact dispatch hop that must fire for the
dooz FAB's clickable to materialize its pointerInput element.
Usage: s141_train41_b.py <apk>
"""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location(
    's41', '/home/z/my-project/scripts/s141_train41_disasm.py')
s41 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s41)
import zipfile as _zf
cd = s41.cd
W = s41.W


def disasm_named(d, cls, meth):
    return s41.disasm(d, cls, meth)


def main():
    apk = sys.argv[1]
    z = zipfile.ZipFile(apk)
    dexes = []
    for name in z.namelist():
        if name.startswith('classes') and name.endswith('.dex'):
            dexes.append((name, cd.Dex(z.read(name))))

    print('=== Luq;.h ref-resolved (the Lpm;.c caller) ===')
    for name, d in dexes:
        for ln in disasm_named(d, 'Luq;', 'h'):
            print(ln)
    print()
    print('=== ALL callers of Luq;.h ===')
    for c in s41.find_all(dexes, 'Luq;', 'h'):
        print(f'  caller {c[0]}.{c[1]} pc={c[2]} op={c[3]:#04x}')
    print()
    print('=== ALL callers of Lq;.h (materialize folder) ===')
    for c in s41.find_all(dexes, 'Lq;', 'h'):
        print(f'  caller {c[0]}.{c[1]} pc={c[2]} op={c[3]:#04x}')


if __name__ == '__main__':
    main()
