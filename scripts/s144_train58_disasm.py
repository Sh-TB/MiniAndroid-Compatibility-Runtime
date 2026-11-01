#!/usr/bin/env python3
"""s144_train58_disasm.py — TRAIN-58: decode Lr;.onLayout (the WALL-STOP method
that never finishes and starves Lt4; of its child layout)."""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location(
    'cd', '/home/z/my-project/scripts/cont9_dexdump.py')
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)

t41spec = importlib.util.spec_from_file_location(
    't41', '/home/z/my-project/scripts/s141_train41_disasm.py')
t41 = importlib.util.module_from_spec(t41spec)
t41spec.loader.exec_module(t41)

apk = sys.argv[1] if len(sys.argv) > 1 else \
    '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'

z = zipfile.ZipFile(apk)
dex = z.read('classes.dex')
d = cd.Dex(dex)

for cls, meth in [('Lr;', 'onLayout'), ('Lho;', 'onLayout'),
                  ('Lr;', 'onMeasure'), ('Lho;', 'onMeasure')]:
    out = t41.disasm(d, cls, meth, tag=f'[{cls}.{meth}] ')
    if not out:
        print(f'-- {cls}.{meth}: NOT FOUND')
        continue
    for line in out[:120]:
        print(line)
    print()
