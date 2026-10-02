#!/usr/bin/env python3
"""S137 — disassemble Le1/d;.g (Gson $Gson$Types.getRawType family) in
opencalculator_53 — pin the instruction at pc=110/113 that throws the
'Expected a Class, ParameterizedType, or GenericArrayType' IAE and the
value shapes feeding it (F-NEW-197-A type-reflection face)."""
import logging, zipfile, sys
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/home/z/my-project/upload/opencalculator_53.apk'
TARGET = 'Le1/d;'

def main():
    z = zipfile.ZipFile(APK)
    dexnames = [n for n in z.namelist() if n.endswith('.dex')]
    for dn in dexnames:
        d = DEX(z.read(dn))
        for c in d.get_classes():
            if c.get_name() != TARGET:
                continue
            print(f"### class {TARGET} extends {c.get_superclassname()}")
            for m in c.get_methods():
                if m.get_name() != 'g':
                    continue
                code = m.get_code()
                bc = code.get_bc()
                print(f"=== g {m.get_descriptor()} ===")
                idx = 0
                for ins in bc.get_instructions():
                    op = ins.get_op_value()
                    name = ins.get_name()
                    operands = []
                    try:
                        for o in ins.get_operands():
                            operands.append(str(o))
                    except Exception:
                        pass
                    mark = ' <<<< THROW-SITE NEIGHBORHOOD' if 100 <= idx <= 116 else ''
                    if 90 <= idx <= 120 or name.startswith('invoke') or 'instance-of' in name or 'const-class' in name:
                        print(f"  {idx:4d}: {name:22s} {' '.join(operands)}{mark}")
                    idx += ins.get_length()
                return
    print('method not found')

if __name__ == '__main__':
    main()
