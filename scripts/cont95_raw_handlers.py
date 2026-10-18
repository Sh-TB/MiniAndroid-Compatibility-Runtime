#!/usr/bin/env python3
"""CONT-95: parse encoded_catch_handler_list raw for o6.I — resolve try[5]'s
handler: typed entries + catch-all, and the handler code address."""
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
                    target = (m, r, d)
                    break
            dexname = dex_name
            break
    if target:
        break

m, raw, d = target
code = m.get_code()
off = code.get_off()
b = raw
p = off
regs, ins_n, outs, tries_n = struct.unpack_from("<HHHH", b, p)
debug_off, insns_n = struct.unpack_from("<II", b, p + 8)
insns_bytes = insns_n * 2
tries_start = p + 16 + insns_bytes
if insns_n % 2 == 1:
    tries_start += 2
handlers_start = tries_start + tries_n * 8

def uleb128(buf, pos):
    result = 0
    shift = 0
    while True:
        byte = buf[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            break
        shift += 7
    return result, pos

def sleb128(buf, pos):
    result = 0
    shift = 0
    while True:
        byte = buf[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        shift += 7
        if not (byte & 0x80):
            break
    if result & (1 << (shift - 1)):
        result -= (1 << shift)
    return result, pos

pos = handlers_start
hsize, pos = uleb128(b, pos)
print(f"handler list at 0x{handlers_start:x}, count={hsize}")

def type_name(tidx):
    # type_ids -> descriptor string
    type_ids_off = d.get_type_ids_off() if hasattr(d, "get_type_ids_off") else None
    try:
        tid = d.get_type_id(tidx)
        sidx = tid.get_descriptor_idx() if hasattr(tid, "get_descriptor_idx") else tid
        return d.get_string(sidx)
    except Exception as e:
        return f"typeidx{tidx}({e})"

for i in range(hsize):
    hpos = pos
    sz, hpos = sleb128(b, hpos)
    entries = []
    for j in range(abs(sz)):
        tidx, hpos = uleb128(b, hpos)
        addr, hpos = uleb128(b, hpos)
        entries.append((addr, type_name(tidx)))
    catch_all = None
    if sz <= 0:
        catch_all, hpos = uleb128(b, hpos)
        entries.append((catch_all, "<catch-all>"))
    print(f"  handler[{i}] @list_off=0x{i} entries={entries}")
    pos = hpos
