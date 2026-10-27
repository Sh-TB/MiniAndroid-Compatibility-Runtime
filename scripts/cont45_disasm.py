#!/usr/bin/env python3
"""CONT-45 D1: proper dex method disassembly via androguard.
Usage: cont45_disasm.py <class-Ldesc> <method> [max_ops]"""
import sys, logging
logging.disable(logging.CRITICAL)
from androguard.core.dex import DEX

d = DEX(open('/tmp/dooz_classes.dex', 'rb').read())
TARGET_CLASS = sys.argv[1] if len(sys.argv) > 1 else 'Lbt0;'
TARGET_METHOD = sys.argv[2] if len(sys.argv) > 2 else 'y0'
MAXOPS = int(sys.argv[3]) if len(sys.argv) > 3 else 400

for m in d.get_methods():
    # d.get_methods() yields MethodIdItem in androguard 4.x; use the
    # class-def methods (EncodedMethod) instead
    pass

for c in d.get_classes():
    if c.get_name() != TARGET_CLASS:
        continue
    for m in c.get_methods():
        if m.get_name() != TARGET_METHOD:
            continue
        code = m.get_code()
        if not code:
            print('no code (abstract/native)')
            sys.exit(0)
        bc = code.get_bc()
        idx = 0
        n = 0
        for ins in bc.get_instructions():
            print(f'{idx:04d} {ins.get_name():30s} {ins.get_output()}')
            idx += ins.get_length()
            n += 1
            if n >= MAXOPS:
                break
        sys.exit(0)
print('NOT FOUND')
