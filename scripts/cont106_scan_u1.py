#!/usr/bin/env python3
"""cont106_scan_u1.py — CONT-106 F-NEW-445 fixture-first step (1):
xref every writer of Lorg/telegram/ui/ActionBar/o6;->u1 (sput-object /
iput-object on xj0) and every constructor/caller of xj0, across all dexes.
Also dumps o6.<clinit> sput inventory + the full o6.k method disasm window.
"""
import sys, zipfile, tempfile, os
from androguard.misc import AnalyzeDex

APK = sys.argv[1] if len(sys.argv) > 1 else "/home/z/my-project/upload/telegram_official.apk"

O6 = "Lorg/telegram/ui/ActionBar/o6;"
XJ0 = "Lorg/telegram/ui/Components/xj0;"

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

writers, xj0_ctors, clinit_sputs = [], [], []
for dexname, d in dexes(APK):
    for c in d.get_classes():
        cn = c.get_name()
        for m in c.get_methods():
            code = m.get_code()
            if code is None:
                continue
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                out = ins.get_output()
                off = getattr(ins, 'get_off', None)
                offhex = hex(off()) if callable(off) else '?'
                # static writers of o6.u1
                if 'sput' in op and O6 + '->u1' in out:
                    writers.append((dexname, cn, m.get_name(), m.get_descriptor(), op, out[:90], offhex))
                # xj0 instantiated anywhere
                if op.startswith('invoke') and XJ0 + '-><init>' in out:
                    xj0_ctors.append((dexname, cn, m.get_name(), op, out[:90], offhex))
                # o6.<clinit> sput inventory
                if cn == O6 and m.get_name() == '<clinit>' and op.startswith('sput'):
                    clinit_sputs.append((op, out[:80], offhex))

print("== WRITERS of o6->u1 (sput) ==", len(writers))
for w in writers: print("  ", w)
print("== xj0.<init> CALLERS ==", len(xj0_ctors))
for w in xj0_ctors[:20]: print("  ", w)
print("== o6.<clinit> sputs ==", len(clinit_sputs))
for w in clinit_sputs[:40]: print("  ", w)
# which fields does clinit NOT set?
import re
sput_fields = set(re.findall(r'->(\w+):', ' '.join(x[1] for x in clinit_sputs)))
print("== clinit sets", len(sput_fields), "fields; u1 in clinit?", 'u1' in sput_fields)
