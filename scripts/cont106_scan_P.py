#!/usr/bin/env python3
"""cont106_scan_P.py — CONT-106 F-NEW-445 step (2):
dump Lorg/telegram/ui/ActionBar/o6;.P(Context) full disasm +
find every caller of o6;.P across all dexes (startup chain).
"""
import sys, zipfile, tempfile, os
from androguard.misc import AnalyzeDex

APK = sys.argv[1] if len(sys.argv) > 1 else "/home/z/my-project/upload/telegram_official.apk"
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

callers = []
P_dumped = False
for dexname, d in dexes(APK):
    for c in d.get_classes():
        cn = c.get_name()
        if cn == O6 and not P_dumped:
            for m in c.get_methods():
                if m.get_name() == 'P':
                    print("== o6.P", m.get_descriptor(), "in", dexname)
                    code = m.get_code()
                    if code:
                        for ins in code.get_bc().get_instructions():
                            print("   ", ins.get_name(), ins.get_output()[:100])
                    P_dumped = True
        for m in c.get_methods():
            code = m.get_code()
            if code is None: continue
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                out = ins.get_output()
                if op.startswith('invoke') and O6 + '->P(' in out:
                    callers.append((dexname, cn, m.get_name(), out[:100]))

print("== CALLERS of o6.P ==", len(callers))
for w in callers: print("  ", w)
