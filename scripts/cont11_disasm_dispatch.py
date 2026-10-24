#!/usr/bin/env python3
"""cont11_disasm_dispatch.py — disassemble Lt4;.dispatchDraw (dooz 23) and
map trace pcs to call targets. Source-first: the bytecode IS the law."""
import sys
from androguard.misc import AnalyzeDex

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"

# extract classes.dex once
import zipfile
with zipfile.ZipFile(APK) as z:
    names = [n for n in z.namelist() if n.endswith('.dex')]
    dex_bytes = {n: z.read(n) for n in names}

target_cls, target_mth = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "dispatchDraw"

import tempfile, os
for n, b in dex_bytes.items():
    p = tempfile.NamedTemporaryFile(suffix=".dex", delete=False)
    p.write(b); p.close()
    a, d, dx = AnalyzeDex(p.name)
    for c in d.get_classes():
        if c.get_name() == target_cls:
            for m in c.get_methods():
                if m.get_name() == target_mth:
                    print(f"== {target_cls}.{target_mth} (dex={n}) ==")
                    code = m.get_code()
                    bc = m.get_instructions()
                    off = 0
                    for ins in bc:
                        op = ins.get_name()
                        out = ins.get_output()
                        print(f"pc={off:4d} {op:28s} {out}")
                        off += ins.get_length() * 2
    os.unlink(p.name)
