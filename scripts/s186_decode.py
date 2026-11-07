#!/usr/bin/env python3
"""s186_decode.py — decode minified classes from a stuck APK's own DEX.

Usage: s186_decode.py <apk> <class1> <class2> ...
Prints for each class: superclass, interfaces, fields, and the bytecode of
<clinit> (or a named method) with referenced classes, so the blocking
library call can be identified from ground truth.
"""
import sys
from androguard.core.apk import APK
from androguard.core.dex import DEX

def clean(name):
    return name.rstrip(';').lstrip('L').replace('/', '.')

def main():
    apk_path = sys.argv[1]
    wanted = sys.argv[2:]
    a = APK(apk_path)
    targets = {w if w.startswith('L') else 'L' + w.replace('.', '/') + ';' for w in wanted}
    found = set()
    for dex_name in a.get_dex_names():
        d = DEX(a.get_dex(dex_name))
        for c in d.get_classes():
            cn = c.get_name()
            if cn in targets:
                found.add(cn)
                print('=' * 70)
                print('CLASS', cn, ' extends ', c.get_superclassname())
                ifs = c.get_interfaces()
                if ifs:
                    print('  implements:', ifs)
                for f in c.get_fields():
                    print('  FIELD', f.get_name(), f.get_descriptor(), 'static' if 'static' in (f.get_access_flags_string() or '') else '')
                for m in c.get_methods():
                    mn = m.get_name()
                    print('-' * 60)
                    print('  METHOD', mn, m.get_descriptor())
                    if mn == '<clinit>' or len(wanted) <= 3:
                        try:
                            for ins in m.get_instructions():
                                op = ins.get_name()
                                out = ins.get_output()
                                print('    ', op, out)
                        except Exception as e:
                            print('     <disasm fail>', e)
    missing = targets - found
    if missing:
        print('NOT FOUND IN DEX:', missing)

if __name__ == '__main__':
    main()
