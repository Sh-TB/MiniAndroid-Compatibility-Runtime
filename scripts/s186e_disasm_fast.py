#!/usr/bin/env python3
"""S186e: targeted fast disassembly (raw DEX parse, no analysis phase).
Usage: s186e_disasm_fast.py <apk> <Lclass;> <method> [descriptor-substr]"""
import logging, sys, zipfile
logging.disable(logging.CRITICAL)
from androguard.core.dex import DEX

apk = sys.argv[1]
cls = sys.argv[2]
meth = sys.argv[3]
dsub = sys.argv[4] if len(sys.argv) > 4 else None

z = zipfile.ZipFile(apk)
for name in [n for n in z.namelist() if n.endswith('.dex')]:
    d = DEX(z.read(name))
    for c in d.get_classes():
        if c.get_name() != cls:
            continue
        for m in c.get_methods():
            if m.get_name() != meth:
                continue
            if dsub and dsub not in m.get_descriptor():
                continue
            print(f"=== {name} {cls} {m.get_name()} {m.get_descriptor()} ===")
            code = m.get_code()
            if code is None:
                print('  (no code)')
                continue
            idx = 0
            for ins in code.get_bc().get_instructions():
                try:
                    out = ins.get_output()
                except Exception as e:
                    out = f'<{e}>'
                print(f'  {idx:04x}: {ins.get_name():22s} {out}')
                idx += ins.get_length()
