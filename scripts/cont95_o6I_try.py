#!/usr/bin/env python3
"""CONT-95: correct androguard-3.3.5 try/handler table for o6.I —
prove whether the createBitmap call site (pc~948..954) is inside a try,
and which handler covers it."""
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

m = next(x for x in o6.get_methods() if x.get_name() == "I" and x.get_code())
code = m.get_code()

# handler list: offset -> description
hl = code.get_handlers()
hmap = {}
try:
    lst = hl.get_list()
except Exception:
    lst = []
for h in lst:
    off = h.get_off()
    entries = []
    try:
        for pair in h.get_handlers():
            tidx = pair.get_type_idx()
            # resolve type name via dex
            tname = d.get_string(tidx) if hasattr(d, "get_string") else f"idx{tidx}"
            entries.append((hex(pair.get_addr()), tname))
    except Exception as e:
        entries.append(("ERR", str(e)))
    ca = h.get_catch_all_addr() if h.get_size() <= 0 else None
    if h.get_size() <= 0:
        entries.append((hex(h.get_catch_all_addr()), "<catch-all>"))
    hmap[off] = entries

tries = code.get_tries()
print(f"try items: {len(tries)}")
for t in tries:
    off = t.get_handler_off()
    print(f"  try [{hex(t.get_start_addr())}..{hex(t.get_start_addr()+t.get_insn_count())}) handler@{hex(off)} -> {hmap.get(off, '???')}")
