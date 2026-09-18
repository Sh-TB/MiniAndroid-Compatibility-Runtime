#!/usr/bin/env python3
"""S57 R-NEW-344: precise androguard disassembly of dooz23 ScatterMap methods.

Dumps Lbw0; (ScatterMap) methods d/f/e/a + Lmg1; helpers with full constant
resolution — ground truth for the nextCapacity(15) -> 31 vs 15 branch.
Usage: s57_andro_lbw0.py [method ...]   (default: d f e a b c)
"""
import sys, zipfile, os, tempfile
from androguard.core.dex import DEX

APK = '/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk'
DEFAULT = ['d', 'f', 'e', 'a', 'b', 'c']


def main():
    z = zipfile.ZipFile(APK)
    tmp = tempfile.mkdtemp()
    dex_path = os.path.join(tmp, 'classes.dex')
    with open(dex_path, 'wb') as fo:
        fo.write(z.read('classes.dex'))
    d = DEX(z.read('classes.dex'))
    want = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT
    for c in d.get_classes():
        cn = c.get_name()
        if cn not in ('Lbw0;', 'Lmg1;'):
            continue
        for m in c.get_methods():
            if m.get_name() not in want:
                continue
            print(f"\n===== {cn}->{m.get_name()}{m.get_descriptor()} =====")
            code = m.get_code()
            if code is None:
                print('  (no code)')
                continue
            pc = 0
            for ins in m.get_instructions():
                name = ins.get_name()
                out = ins.get_output()
                length = ins.get_length()
                print(f"pc={pc:4d} {name:24s} {out}")
                pc += length // 2


if __name__ == '__main__':
    main()
