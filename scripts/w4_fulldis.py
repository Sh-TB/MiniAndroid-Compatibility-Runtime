#!/usr/bin/env python3
"""Full bytecode dump of a method (instructions, branches, fields)."""
import sys, zipfile, re
sys.path.insert(0, '/home/z/my-project/tmp/w4venv/lib/python3.12/site-packages')
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
with zipfile.ZipFile(APK) as z:
    d = DEX(z.read('classes.dex'))

cls, meth = sys.argv[1], sys.argv[2]
desc = sys.argv[3] if len(sys.argv) > 3 else None

for c in d.get_classes():
    if c.get_name() != cls: continue
    for m in c.get_methods():
        if m.get_name() != meth: continue
        if desc and m.get_descriptor() != desc: continue
        code = m.get_code()
        if not code:
            print(f"{cls}.{meth} {m.get_descriptor()} (no code)")
            sys.exit(0)
        print(f"{cls}.{meth} {m.get_descriptor()} regs={code.get_registers_size()} ins={code.get_ins_size()}")
        print("-"*100)
        pc = 0
        for ins in code.get_bc().get_instructions():
            name = ins.get_name()
            length = ins.get_length()
            try:
                out = ins.get_output()
            except Exception:
                out = '?'
            print(f"{pc:5d}: {name:25s} {out.strip()[:130]}")
            pc += length
        print("-"*100)
        # try/catches
        try:
            for t in code.get_tries():
                print(f"TRY {t.get_start_addr():#x}-{t.get_end_addr():#x} catch {t.get_handler()}")
        except Exception:
            pass
        sys.exit(0)
print(f"{cls}.{meth} NOT FOUND")
