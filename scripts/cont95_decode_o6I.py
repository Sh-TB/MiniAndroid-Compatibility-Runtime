#!/usr/bin/env python3
"""CONT-95: decode Lo6;.I (ActionBar ThemeInfo/gradient path) — find the
createBitmap call site and the enclosing try ranges (catch-all handlers)."""
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK_PATH = "upload/telegram_official.apk"

a = APK(APK_PATH)
raw = None
found_dex = []
for dex_name in a.get_dex_names():
    r = a.get_file(dex_name)
    if b"Lorg/telegram/ui/ActionBar/o6;" in r:
        found_dex.append(dex_name)
        d0 = DalvikVMFormat(r)
        for c in d0.get_classes():
            if c.get_name() == "Lorg/telegram/ui/ActionBar/o6;":
                raw = r
                break
    if raw:
        break
print("dex candidates containing 'Lo6;' bytes:", found_dex)
assert raw, "Lo6; not found"
d = DalvikVMFormat(raw)
cls = next(c for c in d.get_classes() if c.get_name() == "Lorg/telegram/ui/ActionBar/o6;")

for m in cls.get_methods():
    if m.get_name() != "I":
        continue
    code = m.get_code()
    print(f"method Lo6;.I {m.get_descriptor()}")
    # try/catch ranges
    tries = code.get_tries()
    print("try items:")
    for t in tries or []:
        hlist = []
        for h in t.get_handlers():
            hlist.append((h.get_instr_offset() if hasattr(h, 'get_instr_offset') else h.get_addr(),
                          h.get_exception_type() if h.get_exception_type() else "<catch-all>"))
        print(f"  start={t.get_start_addr()} len={t.get_insn_count()} end={t.get_start_addr()+t.get_insn_count()} handlers={hlist}")
    print("--- disasm ---")
    addr = 0
    for ins in code.get_bc().get_instructions():
        op = ins.get_name()
        outp = ins.get_output()
        if any(k in outp for k in ("createBitmap", "generateGradient", "getWidth", "getHeight", "sGradient", "invoke")) or op.startswith("const") or op.startswith("aget"):
            print(f"  pc={addr}: {op} {outp}")
        addr += ins.get_length()
