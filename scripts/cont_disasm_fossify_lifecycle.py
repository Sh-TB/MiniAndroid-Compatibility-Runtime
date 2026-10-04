#!/usr/bin/env python3
"""cont_disasm_fossify_lifecycle.py — disassemble the R8-obfuscated
androidx/lifecycle/d.a (pc=62 NPE chain) + y.b (pc=113 CNFE) from
org.fossify.clock to identify the null-Set source (f141-null-recv)."""
import sys
import zipfile
import loguru
loguru.logger.remove()
from androguard.core.dex import DEX as DalvikVMFormat

apk = "/home/z/my-project/run/cont371/store_fossifyclock_0dcf8deddf4c5814/data/app/org.fossify.clock/base.apk"
z = zipfile.ZipFile(apk)

targets = sys.argv[1:] or ["d.a", "y.b"]

for name in z.namelist():
    if not name.endswith(".dex"):
        continue
    d = DalvikVMFormat(z.read(name))
    for m in d.get_methods():
        cls = m.get_class_name()
        meth = m.get_name()
        key = f"{cls}.{meth}"
        if not any(t == f"{cls.split(';')[0].split('/')[-1]}.{meth}" or
                   key.endswith(t) for t in targets):
            continue
        if cls != "Landroidx/lifecycle/d;" and cls != "Landroidx/lifecycle/y;":
            continue
        code = m.get_code()
        if not code:
            continue
        print(f"=== {cls} {meth} {m.get_descriptor()} ===")
        bc = code.get_bc()
        idx = 0
        for ins in bc.get_instructions():
            out = f"  {idx:#06x}: {ins.get_name()} {ins.get_output()}"
            # print window around the divergence pcs
            if idx <= 0x80 or (0xf0 <= idx <= 0x120):
                print(out)
            idx += ins.get_length()
        print()
