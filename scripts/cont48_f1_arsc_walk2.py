#!/usr/bin/env python3
"""cont48_f1_arsc_walk2.py — F1 decode v2: correct string-pool decode +
EXACT mirror of the engine's parse_package walk (NO 4-byte alignment fixup).
Answers: (a) real type-name per type_id, (b) engine-walk drift point,
(c) per-chunk parse_type_chunk sanity (sparse/offset16/dense bounds)."""
import struct, zipfile

apk = "/home/z/my-project/upload/telegram_official.apk"
z = zipfile.ZipFile(apk)
data = z.read("resources.arsc")
N = len(data)
def u16(o): return struct.unpack_from("<H", data, o)[0]
def u32(o): return struct.unpack_from("<I", data, o)[0]

def pool_strings(off):
    pt, ph, ps = u16(off), u16(off+2), u32(off+4)
    str_count = u32(off+8)
    flags = u32(off+16)
    strings_start = u32(off+20)
    start = off + strings_start
    utf8 = (flags & 0x100) != 0
    out = []
    for i in range(str_count):
        o = u32(off + 28 + i*4)
        p = start + o
        if utf8:
            n = data[p]
            if n & 0x80: n = ((n & 0x7f) << 8) | data[p+1]; p += 2
            else: p += 1
            m = data[p]
            if m & 0x80: m = ((m & 0x7f) << 8) | data[p+1]; p += 2
            else: p += 1
            out.append(data[p:p+m].decode("utf-8", "replace"))
        else:
            n = u16(p)
            if n & 0x8000: n = ((n & 0x7fff) << 16) | u16(p+2); p += 4
            else: p += 2
            out.append(data[p:p+n*2].decode("utf-16-le", "replace"))
    return out

# top walk
pos = u16(2)  # after table header
pool_size = u32(pos+4)
pos += pool_size
# package chunk(s)
while pos + 8 <= N:
    ctype, chdr, csize = u16(pos), u16(pos+2), u32(pos+4)
    if ctype == 0x0200: break
    pos += csize
po, pcs, phdr = pos, csize, chdr
ts_off = u32(po+268); ks_off = u32(po+276)
type_strings = pool_strings(po + ts_off)
print("type_strings:", type_strings)

# === ENGINE-EXACT walk (no alignment) ===
p2 = po + phdr
if ts_off and p2 == po + ts_off: p2 += u32(p2+4)
if ks_off and p2 == po + ks_off: p2 += u32(p2+4)
pkg_end = po + pcs
order = []
stop = None
while p2 + 8 <= pkg_end and p2 + 8 <= N:
    ctype, chdr2, csize = u16(p2), u16(p2+2), u32(p2+4)
    if csize == 0:
        stop = ("CSIZE0", p2); break
    name = {0x0201: "TYPE", 0x0202: "SPEC"}.get(ctype, f"UNK{ctype:#06x}")
    det = ""
    if ctype == 0x0201:
        tid = data[p2+8]; flags = data[p2+9]
        ecount = u32(p2+12); estart = u32(p2+16); cfgsz = u32(p2+20)
        tname = type_strings[tid-1] if tid-1 < len(type_strings) else "?"
        arr = ecount*4 if (flags & 1) else ecount*2 if (flags & 2) else ecount*4
        ok_hdr = chdr2 >= 20
        ok_arr = (chdr2 + arr <= csize)
        ok_estart = (estart >= chdr2 + arr and estart <= csize)
        det = (f"tid={tid} '{tname}' ec={ecount} flags={flags:#x} "
               f"hdrOK={ok_hdr} arrOK={ok_arr} esOK={ok_estart}")
        if not (ok_hdr and ok_arr and ok_estart):
            det += "  <<< PARSE-TYPE WOULD FAIL"
        order.append((name, det, p2, csize, tid, tname))
    else:
        order.append((name, f"csize={csize} hdr={chdr2}", p2, csize, None, None))
    p2 += csize
if stop: print("WALK-STOP:", stop)
print(f"chunks walked={len(order)} pkg_end={'yes' if p2==pkg_end else f'{pkg_end-p2} gap'}")
for i,(name,det,off,csz,tid,tname) in enumerate(order):
    print(f"{i:3d} @{off:#08x} sz={csz:6d} {name:6s} {det}")
