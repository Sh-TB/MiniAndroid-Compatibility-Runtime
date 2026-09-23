#!/usr/bin/env python3
"""s90_disasm_full.py — FULL bytecode dump of the F-NEW-162 chain methods."""
import loguru
loguru.logger.remove()
from androguard.core.bytecodes.dvm import DalvikVMFormat
import zipfile

apk = "/home/z/my-project/run/s88/nothanks.apk"
WANT = [
    ("Landroidx/lifecycle/Lifecycling;", "getObserverConstructorType"),
    ("Landroidx/lifecycle/Lifecycling;", "resolveObserverCallbackType"),
    ("Landroidx/lifecycle/Lifecycling;", "lifecycleEventObserver"),
]

z = zipfile.ZipFile(apk)
for name in z.namelist():
    if not name.endswith(".dex"):
        continue
    d = DalvikVMFormat(z.read(name))
    for m in d.get_methods():
        cls = m.get_class_name()
        nm = m.get_name()
        if (cls, nm) not in WANT:
            continue
        code = m.get_code()
        if not code:
            continue
        print(f"=== {cls} {nm}{m.get_descriptor()} ===")
        idx = 0
        for ins in code.get_bc().get_instructions():
            print(f"  {idx:#06x}: {ins.get_name()} {ins.get_output()}")
            idx += ins.get_length()
        print()
