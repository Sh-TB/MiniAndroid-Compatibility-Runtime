#!/usr/bin/env python3
"""cont106_scan_k.py — dump Lorg/telegram/ui/ActionBar/o6;.k (window before 0x100)
to see whether P() or R() is invoked upstream of the pc=46 u1 read.
"""
import sys, zipfile, tempfile, os
from androguard.misc import AnalyzeDex

APK = "/home/z/my-project/upload/telegram_official.apk"
O6 = "Lorg/telegram/ui/ActionBar/o6;"

def dexes(apk):
    with zipfile.ZipFile(apk) as z:
        for name in [n for n in z.namelist() if n.endswith('.dex')]:
            tmp = tempfile.NamedTemporaryFile(suffix='.dex', delete=False)
            tmp.write(z.read(name)); tmp.close()
            try:
                _, d, _ = AnalyzeDex(tmp.name)
            except Exception:
                os.unlink(tmp.name); continue
            yield name, d
            os.unlink(tmp.name)

kcallers = []
for dexname, d in dexes(APK):
    for c in d.get_classes():
        cn = c.get_name()
        if cn == O6:
            for m in c.get_methods():
                if m.get_name() == 'k':
                    print("== o6.k", m.get_descriptor(), dexname)
                    code = m.get_code()
                    off = 0
                    for ins in code.get_bc().get_instructions():
                        sz = ins.get_length()
                        print("   ", hex(off), ins.get_name(), ins.get_output()[:95])
                        off += sz
                        if off > 0x200: break
        for m in c.get_methods():
            code = m.get_code()
            if code is None: continue
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                out = ins.get_output()
                if op.startswith('invoke') and O6 + '->k(' in out:
                    kcallers.append((dexname, cn, m.get_name(), out[:100]))

print("== CALLERS of o6.k ==", len(kcallers))
for w in kcallers[:10]: print("  ", w)
