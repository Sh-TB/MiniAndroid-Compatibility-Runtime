#!/usr/bin/env python3
"""S88 androguard method disassembler — SOURCE-FIRST first-divergence tool.
Usage: python3.13 s88_disasm.py <apk> <Lclass;> <method> [max_lines]"""
import sys
from androguard.misc import AnalyzeDex
import zipfile, tempfile, os

apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
maxl = int(sys.argv[4]) if len(sys.argv) > 4 else 60

z = zipfile.ZipFile(apk)
tmp = tempfile.mkdtemp()
paths = []
for n in z.namelist():
    if n.endswith('.dex'):
        p = os.path.join(tmp, n)
        open(p, 'wb').write(z.read(n))
        paths.append(p)

for p in paths:
    a, d, dx = AnalyzeDex(p)
    for m in d.get_methods():
        if m.get_class_name() == cls and m.get_name() == meth:
            print(f'=== {cls}.{meth} in {os.path.basename(p)}')
            code = m.get_code()
            if code is None:
                print('  (no code)')
                continue
            bc = m.get_instructions()
            for i, ins in enumerate(bc):
                if i >= maxl: print('  ...'); break
                print(f'  {ins.get_name():26s} {ins.get_output()}')
            sys.exit(0)
print('NOT FOUND', cls, meth)
