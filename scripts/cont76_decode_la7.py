#!/usr/bin/env python3
"""CONT-76 v2: robust decode of La7.m bytecode + Lzs.m caller window (dooz).

F-NEW-378 evidence: the naked unwind La7.m -> Lzs.m(measure) needs the exact
callee shape. This script:
1. Dumps La7.m raw code units + parses the throw window around pc=0x20..0x24.
2. Dumps Lzs.m FULL disassembly, marking the invoke at pc=0x4a.
3. Decodes Lr50; (the functional interface) and Lmq; (continuation?).
"""
import logging
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
import zipfile
from androguard.core.dex import DEX

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
WANT = {"La7;", "Lzs;", "Lr50;", "Lmq;"}


def dump_method(m, label, mark_pc=None):
    code = m.get_code()
    print(f"--- {label}: {m.get_name()} {m.get_descriptor()} ---")
    if code is None:
        print("    <no code>")
        return
    bc = code.get_bc()
    try:
        ins_list = list(bc.get_instructions())
    except Exception as e:
        print(f"    <instruction iteration failed: {e}>")
        return
    off = 0
    for ins in ins_list:
        try:
            ln = ins.get_length()
        except Exception:
            ln = 2
        mark = " <== invoke_pc" if mark_pc is not None and off == mark_pc else ""
        try:
            print(f"    {off:04x}: {ins.get_name():26s} {ins.get_output()}{mark}")
        except Exception as e:
            print(f"    {off:04x}: <decode error {e}>{mark}")
        off += ln


def main():
    z = zipfile.ZipFile(APK)
    for dname in [n for n in z.namelist()
                  if n.startswith("classes") and n.endswith(".dex")]:
        d = DEX(z.read(dname))
        for c in d.get_classes():
            try:
                cn = c.get_name()
            except Exception:
                continue
            if cn not in WANT:
                continue
            print("=" * 92)
            print(f"CLASS {cn} (in {dname}) extends {c.get_superclassname()}"
                  f" ifc={list(c.get_interfaces())}")
            for f in c.get_fields():
                print(f"  field {f.get_name()} : {f.get_descriptor()}")
            for m in c.get_methods():
                print(f"  method {m.get_name()} {m.get_descriptor()} "
                      f"[{m.get_access_flags_string()}]")
            # full disasm for the two key methods
            for m in c.get_methods():
                name = m.get_name()
                if cn == "La7;" and name == "m":
                    dump_method(m, f"{cn}", )
                elif cn == "Lzs;" and name == "m":
                    dump_method(m, f"{cn}", mark_pc=0x4a)
                elif cn == "Lr50;":
                    dump_method(m, f"{cn}")


if __name__ == "__main__":
    main()
