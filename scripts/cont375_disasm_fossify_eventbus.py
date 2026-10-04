#!/usr/bin/env python3
"""cont375 — disassemble LO5/d;.i (EventBus SubscriberMethodFinder family)
in org.fossify.clock_10.apk: pin the pc=392 EventBusException construction,
the modifier/parameter queries that feed it, and the getDeclaredMethods
consumers — evidence for R-NEW-464 Method-record reflection routing."""
import logging, zipfile, sys
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = '/home/z/my-project/tmp/diff366_apks/org.fossify.clock_10.apk'
TARGET = 'LO5/d;'
METHODS = ('i', 'a', 'b', 'c')

def main():
    z = zipfile.ZipFile(APK)
    for dn in [n for n in z.namelist() if n.endswith('.dex')]:
        raw = z.read(dn)
        # quick class-presence scan via mutf8 name
        if b'LO5/d;' not in raw:
            continue
        d = DalvikVMFormat(raw)
        for c in d.get_classes():
            if c.get_name() != TARGET:
                continue
            print(f"### class {TARGET} extends {c.get_superclassname()}")
            for m in c.get_methods():
                if m.get_name() not in METHODS:
                    continue
                code = m.get_code()
                if code is None:
                    continue
                print(f"\n### method {m.get_name()} {m.get_descriptor()} "
                      f"regs={code.get_registers_size()} ins={code.get_ins_size()}")
                bc = code.get_bc()
                idx = 0
                for ins in bc.get_instructions():
                    op = ins.get_name()
                    out = f"  pc={idx:5d} {op:32s} {ins.get_output()}"
                    if 'const-string' in op or 'invoke' in op or \
                       'iget' in op or 'new-instance' in op:
                        print(out)
                    idx += ins.get_length()

if __name__ == '__main__':
    main()
