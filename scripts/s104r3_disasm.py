#!/usr/bin/env python3
"""S104-r3: disassemble dooz v23 compose-frontier classes (Lt4;.L, Lsr;.run).
Usage: s104r3_disasm.py <Lclass;> <method> [descriptor-substr]
"""
import logging, sys, zipfile
logging.disable(logging.CRITICAL)
from androguard.core.dex import DEX

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'

def main():
    cls = sys.argv[1]
    meth = sys.argv[2]
    dsub = sys.argv[3] if len(sys.argv) > 3 else None
    z = zipfile.ZipFile(APK)
    d = DEX(z.read('classes.dex'))
    found = False
    for c in d.get_classes():
        if c.get_name() != cls:
            continue
        for m in c.get_methods():
            if m.get_name() != meth:
                continue
            if dsub and dsub not in m.get_descriptor():
                continue
            found = True
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
    if not found:
        print(f"NOT FOUND: {cls}.{meth} {dsub or ''}")
        print("classes containing '" + cls + "':")
        for c in d.get_classes():
            if cls.rstrip(';') in c.get_name():
                print("  ", c.get_name(), "methods:", [m.get_name() for m in c.get_methods()][:12])

if __name__ == '__main__':
    main()
