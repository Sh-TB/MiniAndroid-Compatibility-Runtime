#!/usr/bin/env python3
"""cont30_disasm.py — CONT-30 ground-truth Dalvik disassembler (androguard
DalvikVMFormat API installed in this container).

usage: cont30_disasm.py <apk> <class-desc-with-semicolons> [cap]
       cont30_disasm.py <apk> --scan <name-substr>   # locate classes/methods

Prints every instruction of the matched class's methods with pc, name,
output. Ground truth for the GapComposer differ decode (CONT-29 §8 target).
"""
import sys, io, zipfile
from androguard.core.bytecodes.dvm import DalvikVMFormat


def load_dexes(apk):
    raw = open(apk, "rb").read()
    zf = zipfile.ZipFile(io.BytesIO(raw))
    out = []
    for n in sorted(x for x in zf.namelist() if x.endswith(".dex")):
        out.append((n, DalvikVMFormat(zf.read(n))))
    return out


def main():
    apk = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else ""
    cap = 3000
    if mode == "--scan":
        want = sys.argv[3].lower()
        for dn, d in load_dexes(apk):
            for c in d.get_classes():
                cn = c.get_name()
                if want in cn.lower():
                    for m in c.get_methods():
                        code = m.get_code()
                        units = code.get_insns_size() if code else 0
                        print(f"{dn} {cn}.{m.get_name()}{m.get_descriptor()} units={units}")
        return
    cls = sys.argv[2]
    if len(sys.argv) > 3:
        cap = int(sys.argv[3])
    only = sys.argv[4] if len(sys.argv) > 4 else None
    for dn, d in load_dexes(apk):
        for c in d.get_classes():
            if c.get_name() != cls:
                continue
            for m in c.get_methods():
                if only and m.get_name() != only:
                    continue
                code = m.get_code()
                if not code:
                    print(f"{dn} {cls}.{m.get_name()}{m.get_descriptor()} <no code>")
                    continue
                print(f"{dn} {cls}.{m.get_name()}{m.get_descriptor()} "
                      f"regs={code.get_registers_size()} ins={code.get_ins_size()} "
                      f"units={code.get_insns_size()}")
                idx = 0
                for ins in code.get_bc().get_instructions():
                    print(f"  @{idx:#06x} {ins.get_name():<24} {ins.get_output()}")
                    idx += ins.get_length() // 2
                    if idx > cap:
                        print("  ...(capped)")
                        break


if __name__ == "__main__":
    main()
