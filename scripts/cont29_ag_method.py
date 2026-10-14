#!/usr/bin/env python3
"""cont29_ag_method.py — disassemble EXACT method (class + full name).
usage: cont29_ag_method.py <apk> <class-desc> <exact-name> [max]
"""
import sys, io, zipfile
from androguard.core.dex import DEX
apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
cap = int(sys.argv[4]) if len(sys.argv) > 4 else 250
raw = open(apk, "rb").read()
zf = zipfile.ZipFile(io.BytesIO(raw))
for n in [x for x in zf.namelist() if x.endswith(".dex")]:
    d = DEX(zf.read(n))
    for c in d.get_classes():
        if c.get_name() != cls: continue
        for m in c.get_methods():
            if m.get_name() != meth: continue
            code = m.get_code()
            if not code:
                print(f"{cls}.{m.get_name()}{m.get_descriptor()} <no code>"); continue
            print(f"{cls}.{m.get_name()}{m.get_descriptor()}  regs={code.get_registers_size()} ins={code.get_ins_size()} insns={code.get_insns_size()}")
            idx = 0
            for ins in code.get_bc().get_instructions():
                print(f"  @{idx:#06x} {ins.get_name():<22} {ins.get_output()}")
                idx += ins.get_length() // 2
                if idx > cap:
                    print("  ...(capped)"); sys.exit(0)
