#!/usr/bin/env python3
"""cont106_scan_n2r.py — CONT-106 U-n2r: precise disasm of the telegram
protobuf-lite OOB family: n2.r (the crash site), n2.B (the name-walk),
s2 (MessageInfo construction), and the MessageSchema ctor aget @0x568.
Finds: every aget-object in n2.r with surrounding loop bounds; every
array-length; every getDeclaredField/Unsafe call in n2.B.
"""
import sys, zipfile, tempfile, os
from androguard.misc import AnalyzeDex

APK = "/home/z/my-project/upload/telegram_official.apk"
TARGETS = None  # full-package filter below

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

seen = set()
for dexname, d in dexes(APK):
    for c in d.get_classes():
        cn = c.get_name()
        if not (cn.startswith("Lcom/google/android/gms/internal/play_billing/") or cn.startswith("Lcom/android/billingclient/")):
            continue
        for m in c.get_methods():
            key = (cn, m.get_name(), m.get_descriptor())
            if key in seen:
                continue
            code = m.get_code()
            if code is None:
                continue
            has_aget = False
            ins_list = []
            off = 0
            for ins in code.get_bc().get_instructions():
                nm = ins.get_name()
                out = ins.get_output()
                if nm.startswith('aget'):
                    has_aget = True
                ins_list.append((off, nm, out[:100]))
                off += ins.get_length()
            # dump n2.r fully; others only if they contain aget-object
            if cn.endswith("/n2;") or (has_aget and ("billing" in cn)):
                seen.add(key)
                print(f"== {cn} {m.get_name()} {m.get_descriptor()} ({dexname}) insns={len(ins_list)}")
                for o, nm, out in ins_list[:400]:
                    print("   ", hex(o), nm, out)
