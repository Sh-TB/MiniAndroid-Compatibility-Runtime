#!/usr/bin/env python3
"""CONT-95: disasm Lo6;.I around pc=951 (createBitmap(0,0) call site) + trace
which registers feed w/h; also list yc0.h pc~92 region and SvgHelper decode path."""
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
        print("(o6 in", dex_name, ")")
        break

for m in o6.get_methods():
    if m.get_name() != "I":
        continue
    code = m.get_code()
    if not code:
        continue
    print(f"### method I {m.get_descriptor()}")
    tries = None
    try:
        tries = code.get_tries()
        print("  get_tries ->", repr(tries)[:400])
    except Exception as e:
        print("  get_tries RAISED:", type(e).__name__, str(e)[:200])
        # raw inspection
        print("  code items:", repr(code)[:600])
    if tries:
        for t in tries:
            hs = []
            for h in t.get_handlers() or []:
                et = h.get_exception_type()
                hs.append((hex(h.get_addr()), et if et else "<catch-all>"))
            print(f"  try [{hex(t.get_start_addr())}..{hex(t.get_start_addr()+t.get_insn_count())}) handlers={hs}")
    else:
        print("  (no try items)")
    addr = 0
    insns = []
    for ins in code.get_bc().get_instructions():
        insns.append((addr, ins.get_name(), ins.get_output()))
        addr += ins.get_length()
    for a2, op, out in insns:
        if 780 <= a2 <= 1010:
            print(f"  pc={a2}: {op} {out}")
