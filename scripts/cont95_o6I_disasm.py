#!/usr/bin/env python3
"""CONT-95: pure disasm of o6.I — window + full listing to file. No try-table."""
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK_PATH = "upload/telegram_official.apk"

a = APK(APK_PATH)
o6 = None
for dex_name in a.get_dex_names():
    r = a.get_file(dex_name)
    d = DalvikVMFormat(r)
    for c in d.get_classes():
        if c.get_name() == "Lorg/telegram/ui/ActionBar/o6;":
            o6 = c
            break
    if o6:
        break

m = next(x for x in o6.get_methods() if x.get_name() == "I" and x.get_code())
code = m.get_code()
print(f"### o6.I {m.get_descriptor()}")
addr = 0
for ins in code.get_bc().get_instructions():
    a2 = addr
    op = ins.get_name()
    out = ins.get_output()
    if 1660 <= a2 <= 1902:
        print(f"  pc={a2}: {op} {out}")
    addr += ins.get_length()
