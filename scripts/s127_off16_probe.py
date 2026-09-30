#!/usr/bin/env python3
"""S127 — derive the TRUE OFFSET16 position law by locating the real bytes."""
import struct

d = open("miniandroid/framework_res/resources.arsc", "rb").read()
def rd16(b, o): return struct.unpack_from("<H", b, o)[0]
def rd32(b, o): return struct.unpack_from("<I", b, o)[0]

# type-6 (color) default OFF16 chunk found by audit at 19373444
CH = 19373444
ihs = rd16(d, CH + 2)
flags = d[CH + 9]
ecnt = rd32(d, CH + 12)
estart = rd32(d, CH + 16)
print(f"chunk@{CH} hdrSize={ihs} flags=0x{flags:02x} ecnt={ecnt} entriesStart={estart}")
arr = CH + ihs
for idx in (0x0E, 0x0F):
    o16 = rd16(d, arr + 2 * idx)
    print(f"off16[{idx:#06x}] = {o16:#06x}  -> *4 = {o16*4}, *2 = {o16*2}, raw = {o16}")
    for k, label in ((4, "*4"), (2, "*2"), (1, "*1")):
        pos = estart + o16 * k
        ep = CH + pos
        esz = rd16(d, ep)
        print(f"   law {label}: pos={pos} entry hdr size={esz} raw={d[ep:ep+16].hex()}")

# Search the whole chunk for the true Res_value bytes:
# background_dark  = 08 00 00 1c 00 00 00 ff  (#ff000000, ARGB8)
# background_light = 08 00 00 1c ff ff ff ff  (#ffffffff)
targets = {"#ff000000": bytes.fromhex("0800001c000000ff"),
           "#ffffffff": bytes.fromhex("0800001cffffffff")}
for name, pat in targets.items():
    start, pos_found = CH, []
    while True:
        i = d.find(pat, start, CH + rd32(d, CH + 4))
        if i < 0: break
        pos_found.append(i - CH - estart)  # delta from entriesStart
        start = i + 1
    print(f"{name}: found at deltas-from-entriesStart: {pos_found}")
    for delta in pos_found:
        # which off16 entry maps here under which law?
        for idx in (0x0E, 0x0F):
            o16 = rd16(d, arr + 2 * idx)
            if o16 and delta % o16 == 0:
                pass
        print(f"   delta={delta}: /1={delta} as off16 candidate")
