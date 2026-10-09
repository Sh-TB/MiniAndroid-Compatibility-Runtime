#!/usr/bin/env python3
"""cont29_ag_disasm.py — ground-truth method disassembly via androguard.
usage: cont29_ag_disasm.py <apk> <class-desc> <method-substr> [max-insns]
Accepts APK (zip) or raw .dex. Handles $ in method names (exact or substring).
"""
import sys, zipfile, io
from androguard.core.dex import DEX

def main():
    apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
    cap = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    raw = open(apk, "rb").read()
    if raw[:2] == b"PK":
        zf = zipfile.ZipFile(io.BytesIO(raw))
        dexes = [DEX(zf.read(n)) for n in zf.namelist() if n.endswith(".dex")]
    else:
        dexes = [DEX(raw)]
    for d in dexes:
        for c in d.get_classes():
            if c.get_name() != cls:
                continue
            for m in c.get_methods():
                if meth not in m.get_name():
                    continue
                code = m.get_code()
                print(f"{cls}.{m.get_name()}{m.get_descriptor()}  "
                      f"regs={code.get_registers_size()} ins={code.get_ins_size()} "
                      f"insns={code.get_insns_size()}")
                idx = 0
                for ins in code.get_bc().get_instructions():
                    print(f"  @{idx:#06x} {ins.get_name():<24} {ins.get_output()}")
                    idx += ins.get_length() // 2
                    if idx > cap:
                        print("  ... (capped)")
                        return
                return
    print(f"NOT FOUND: {cls} {meth}")

if __name__ == "__main__":
    main()
