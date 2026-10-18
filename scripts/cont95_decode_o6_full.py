#!/usr/bin/env python3
"""CONT-95: full try/catch table for org.telegram.ui.ActionBar.o6 (all dexes),
org.telegram.ui.Components.yc0, and locate createBitmap w=0 call sites."""
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK_PATH = "upload/telegram_official.apk"
TARGETS = {"Lorg/telegram/ui/ActionBar/o6;", "Lorg/telegram/ui/Components/yc0;"}

a = APK(APK_PATH)
seen = {}
for dex_name in a.get_dex_names():
    r = a.get_file(dex_name)
    d = DalvikVMFormat(r)
    for c in d.get_classes():
        n = c.get_name()
        if n in TARGETS and n not in seen:
            seen[n] = (dex_name, c)

for n, (dx, c) in seen.items():
    print(f"### {n} (in {dx})")
    for m in c.get_methods():
        code = m.get_code()
        if not code:
            continue
        tries = code.get_tries()
        # does this method contain createBitmap / generateGradient invokes?
        kinds = set()
        addr = 0
        invsites = []
        for ins in code.get_bc().get_instructions():
            op = ins.get_name()
            outp = ins.get_output()
            if op.startswith("invoke") and ("createBitmap" in outp or "generateGradient" in outp):
                invsites.append((addr, outp.split(",")[0].strip()))
            addr += ins.get_length()
        if tries or invsites:
            print(f"  method {m.get_name()} {m.get_descriptor()[:80]}")
            for t in tries or []:
                hs = []
                for h in t.get_handlers() or []:
                    et = h.get_exception_type()
                    hs.append((hex(h.get_addr() if hasattr(h,'get_addr') else 0), et if et else "<catch-all>"))
                print(f"    try [{hex(t.get_start_addr())}..{hex(t.get_start_addr()+t.get_insn_count())}) handlers={hs}")
            for a2, i2 in invsites:
                print(f"    invoke@{hex(a2)}: {i2}")
