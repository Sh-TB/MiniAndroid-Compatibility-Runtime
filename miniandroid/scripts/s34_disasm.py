#!/usr/bin/env python3
"""S34: decompile a method's bytecode from dooz APK with full resolution.
Usage: s34_disasm.py <Lclass;> <method> [descriptor-substr]
Ground-truth DEX tooling (androguard 4.x EncodedMethod API).
"""
import logging, sys, zipfile
logging.disable(logging.CRITICAL)
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk'


def main():
    cls = sys.argv[1]
    meth = sys.argv[2]
    dsub = sys.argv[3] if len(sys.argv) > 3 else None
    z = zipfile.ZipFile(APK)
    d = DEX(z.read('classes.dex'))
    for c in d.get_classes():
        if c.get_name() != cls:
            continue
        for m in c.get_methods():
            if m.get_name() != meth:
                continue
            if dsub and dsub not in m.get_descriptor():
                continue
            print(f"=== {cls}.{m.get_name()} {m.get_descriptor()} ===")
            code = m.get_code()
            if code is None:
                print('  (no code — abstract/native)')
                continue
            bc = code.get_bc()
            idx = 0
            for ins in bc.get_instructions():
                try:
                    out = ins.get_output()
                except Exception as e:
                    out = f'<{e}>'
                print(f'  {idx:04x}: {ins.get_name()} {out}')
                idx += ins.get_length()
            return
    print('NOT FOUND')


if __name__ == '__main__':
    main()
