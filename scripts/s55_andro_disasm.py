#!/usr/bin/env python3
# S55 R-NEW-361 recon: precise androguard disassembly of the dooz v18
# ScatterMap-face methods (Lh/r;.c findImpl, LP/v$a;.c set-with-insertion).
import sys
sys.path.insert(0, '/home/z/.local/lib/python3.13/site-packages')
from androguard.misc import AnalyzeDex
import zipfile, os, tempfile

apk = zipfile.ZipFile('/home/z/my-project/miniandroid/download/exp076_corpus/io.github.yamin8000.dooz_18.apk')
tmp = tempfile.mkdtemp()
dex_path = os.path.join(tmp, 'classes.dex')
with open(dex_path, 'wb') as f:
    f.write(apk.read('classes.dex'))

a, d, dx = AnalyzeDex(dex_path)

want = sys.argv[1:] if len(sys.argv) > 1 else ['Lh/r;->c', 'LP/v$a;->c', 'Lh/r;->a', 'Lh/r;->b', 'Lh/r;->d']
for m in d.get_methods():
    sig = f"{m.get_class_name()}->{m.get_name()}"
    if sig not in want:
        continue
    print(f"\n===== {sig}{m.get_descriptor()} =====")
    code = m.get_code()
    if code is None:
        print("  (no code)")
        continue
    bc = m.get_instructions()
    pc = 0
    for ins in bc:
        op = ins.get_name()
        operands = ins.get_output()
        print(f"  pc={pc:5d} {op:28s} {operands}")
        pc += ins.get_length()
