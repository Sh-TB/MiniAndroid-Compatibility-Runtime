#!/usr/bin/env python3
"""s90_disasm_lifecycling.py — disassemble Lifecycling.resolveObserverCallbackType
from nothanks.apk to identify the exact invoke at pc 0x7e (F-NEW-162 root)."""
import sys
import loguru
loguru.logger.remove()
from androguard.core.bytecodes.dvm import DalvikVMFormat
import zipfile

apk = "/home/z/my-project/run/s88/nothanks.apk"
z = zipfile.ZipFile(apk)
targets = sys.argv[1:] or [
    "Landroidx/lifecycle/Lifecycling;.resolveObserverCallbackType",
    "Landroidx/lifecycle/Lifecycling;.getObserverConstructorType",
]

for name in z.namelist():
    if not name.endswith(".dex"):
        continue
    d = DalvikVMFormat(z.read(name))
    for m in d.get_methods():
        key = f"{m.get_class_name()}.{m.get_name()}"
        if not any(t.split('.')[-1] in m.get_name() and
                   t.split(';')[0].split('/')[-1] in m.get_class_name()
                   for t in targets):
            continue
        code = m.get_code()
        if not code:
            continue
        print(f"=== {m.get_class_name()} {m.get_name()}"
              f"{m.get_descriptor()} ===")
        bc = code.get_bc()
        idx = 0
        for ins in bc.get_instructions():
            op = ins.get_name()
            if idx >= 0x100:
                break
            out = f"  {idx:#06x}: {op} {ins.get_output()}"
            if 0x60 <= idx <= 0xA0:
                print(out)
            idx += ins.get_length()
        print()
