#!/usr/bin/env python3
"""S58 R-NEW-376: forensic disassembly of the dooz v23 ctor-climb face classes.

Dumps ALL <init> overloads of Lgz1; and Lbp1; (+ their superclass chains and
the init-state relevant fields) with full constant resolution — ground truth
for the self-delegation question: does gz1.<init>(X) invoke gz1.<init>(X)
(illegal) or a DIFFERENT overload (legal climb)?

Also maps every invoke-direct* in the two classes to its resolved target.
Usage: s58_gz1_forensic.py [class ...]   (default: Lgz1; Lbp1;)
"""
import sys, zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = '/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk'
DEFAULT = ['Lgz1;', 'Lbp1;']


def load():
    z = zipfile.ZipFile(APK)
    return DEX(z.read('classes.dex'))


def dump_class(d, cn, init_only=True, method_filter=None):
    cls = None
    names = []
    for c in d.get_classes():
        n = c.get_name()
        if n == cn:
            cls = c
            break
        if cn.strip('L;') in n:
            names.append(n)
    if cls is None:
        print(f"\n##### {cn}: NOT IN DEX (fuzzy hits: {names[:8]})")
        return
    sname = cls.get_superclassname()
    print(f"\n##### {cn} extends {sname}")
    # fields (init-state)
    for f in cls.get_fields():
        print(f"  field {f.get_name()} : {f.get_descriptor()} access={f.get_access_flags_string()}")
    for m in cls.get_methods():
        if method_filter is not None and m.get_name() not in method_filter:
            continue
        if not method_filter and init_only and m.get_name() != '<init>':
            continue
        code = m.get_code()
        print(f"\n===== {cn}->{m.get_name()}{m.get_descriptor()} "
              f"regs={code.get_registers_size() if code else '?'} "
              f"ins={code.get_ins_size() if code else '?'} "
              f"insns={code.get_length()//2 if code else 0}")
        if code is None:
            print('  (abstract/native)')
            continue
        pc = 0
        for ins in m.get_instructions():
            name = ins.get_name()
            out = ins.get_output()
            print(f"pc={pc:4d} {name:26s} {out}")
            pc += ins.get_length() // 2


def main():
    d = load()
    want = [a for a in sys.argv[1:] if not a.startswith('--')]
    all_methods = '--all' in sys.argv
    for cn in want:
        dump_class(d, cn, init_only=not all_methods,
                   method_filter=None if not all_methods else
                   None)


if __name__ == '__main__':
    main()
