#!/usr/bin/env python3
"""CONT-95: GROUND-TRUTH raw DEX try-table parse for o6.I (no androguard wrappers).
Locate the method's code_item offset via androguard, then parse:
  code_item: registers(2) ins(2) outs(2) tries(2) debug_off(4) insns(4) insns[..] pad tries[] handlers[]
U16 units for insns; try_item = start(4) insn_count(2) handler_off(2)."""
import struct
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK_PATH = "upload/telegram_official.apk"

a = APK(APK_PATH)
target = None
dexname = None
for dex_name in a.get_dex_names():
    r = a.get_file(dex_name)
    d = DalvikVMFormat(r)
    for c in d.get_classes():
        if c.get_name() == "Lorg/telegram/ui/ActionBar/o6;":
            for m in c.get_methods():
                if m.get_name() == "I" and m.get_code():
                    target = (m, r)
                    break
            dexname = dex_name
            break
    if target:
        break

m, raw = target
code = m.get_code()
# androguard DalvikCode offset:
off = None
for attr in ("get_offset", "get_code_offset", "offset"):
    if hasattr(code, attr):
        off = getattr(code, attr)
        if callable(off):
            off = off()
        break
print("dex:", dexname, "code offset:", hex(off) if off else None)

if off is not None:
    b = raw
    p = off
    regs, ins_n, outs, tries_n = struct.unpack_from("<HHHH", b, p)
    debug_off, insns_n = struct.unpack_from("<II", b, p + 8)
    print(f"registers={regs} ins={ins_n} outs={outs} tries_count={tries_n} insns_units={insns_n}")
    insns_bytes = insns_n * 2
    tries_start = p + 16 + insns_bytes
    if insns_n % 2 == 1:
        tries_start += 2  # 4-byte padding
    print("tries table at", hex(tries_start))
    for i in range(tries_n):
        start, cnt, hoff = struct.unpack_from("<IHH", b, tries_start + i * 8)
        print(f"  try[{i}] start={start} (0x{start:x}) count={cnt} end={start+cnt} (0x{start+cnt:x}) handler_off={hoff} (0x{hoff:x})")
    # window check
    for probe in (944, 948, 954, 962, 994):
        covered = 0
    print("createBitmap call site pcs: 944/948/954/962; move-exception pc=994")
