#!/usr/bin/env python3
"""cont48_f1_arsc_walk.py — F1 pre-decode: raw chunk walk of telegram's
resources.arsc. Lists every TYPE (0x0201) chunk in order with type_id,
entry_count, flags(SPARSE/OFFSET16), header_size, entries_start, config size —
then reproduces the engine walk (csize==0 break / drift law) and names where
the plurals (type 0x0f) chunks sit relative to any walk-stopping anomaly."""
import struct, sys, zipfile, json

apk = "/home/z/my-project/upload/telegram_official.apk"
z = zipfile.ZipFile(apk)
data = z.read("resources.arsc")
print(f"arsc bytes={len(data)}")

def u16(o): return struct.unpack_from("<H", data, o)[0]
def u32(o): return struct.unpack_from("<I", data, o)[0]

total_size = u32(4)
print(f"table total_size={total_size} file_match={total_size==len(data)}")

# package chunk walk (mirror arsc_parser.cpp parse_package)
# top: RES_TABLE_TYPE (0x0002) header; global string pool follows header
tbl_hdr = u16(2)
pos = tbl_hdr
# global string pool
pool_type, pool_hdr, pool_size = u16(pos), u16(pos+2), u32(pos+4)
print(f"global pool type={pool_type:#06x} hdr={pool_hdr} size={pool_size}")
pos += pool_size

# expect package chunk(s)
pkgs = []
while pos + 8 <= len(data):
    ctype, chdr, csize = u16(pos), u16(pos+2), u32(pos+4)
    if ctype == 0x0200:
        pkgs.append((pos, csize, chdr))
    pos += csize
    if csize == 0:
        print(f"WALK-BREAK csize==0 at {pos:#x}")
        break
print(f"packages={len(pkgs)}")

for po, pcs, phdr in pkgs:
    pkg_id = u32(po+8)
    ts_off = u32(po+268)
    ks_off = u32(po+276)
    print(f"\nPACKAGE id={pkg_id:#x} hdr={phdr} csize={pcs} typeStrings={ts_off:#x} keyStrings={ks_off:#x}")
    # type strings pool (to name type indices)
    tsp = po + ts_off
    def pool_strings(off):
        pt, ph, ps = u16(off), u16(off+2), u32(off+4)
        str_count = u32(off+8)
        flags = u32(off+16)
        start = off + ph
        utf8 = (flags & 0x100) != 0
        out = []
        for i in range(str_count):
            # offsets array of u32
            so = off + 28 + i*4 if True else 0
            o = u32(off + 28 + i*4)
            p = start + o
            if utf8:
                # u16 len (utf16), u8/u16 len (utf8), bytes
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
    type_strings = pool_strings(tsp)
    print(f"type_strings n={len(type_strings)}: {type_strings}")
    print(f"plurals type index (1-based resid byte): {[i+1 for i,s in enumerate(type_strings) if 'plural' in s.lower()]}")

    # inner walk after header
    p2 = po + phdr
    if ts_off and p2 == po + ts_off: p2 += u32(p2+4)
    if ks_off and p2 == po + ks_off: p2 += u32(p2+4)
    pkg_end = po + pcs
    types = []
    walk_stop = None
    while p2 + 8 <= pkg_end:
        ctype, chdr, csize = u16(p2), u16(p2+2), u32(p2+4)
        if csize == 0:
            walk_stop = ("csize==0", p2)
            break
        if ctype == 0x0201:
            tid = data[p2+8]
            flags = data[p2+9]
            res0 = data[p2+10]
            ecount = u32(p2+12)
            estart = u32(p2+16)
            cfgsize = u32(p2+20)
            types.append((tid, ecount, flags, chdr, estart, cfgsize, csize, res0))
        elif ctype != 0x0202:
            walk_stop = (f"unknown {ctype:#06x}", p2)
        p2 += csize
        if p2 % 4: p2 += 4 - (p2 % 4)   # engine does NOT align; note drift points
    print(f"walk_stop={walk_stop} end_gap={pkg_end - p2 if p2<=pkg_end else 'OVERSHOT'}")
    bytid = {}
    for t in types:
        bytid.setdefault(t[0], []).append(t)
    print(f"TYPE chunks total={len(types)} distinct type_ids={sorted(bytid)}")
    for tid in sorted(bytid):
        name = type_strings[tid-1] if tid-1 < len(type_strings) else "?"
        chs = bytid[tid]
        fl = lambda f: ("SPARSE" if f & 1 else "") + ("OFFSET16" if f & 2 else "")
        print(f"  type {tid:#04x} '{name}': {len(chs)} chunks, entries={[c[1] for c in chs][:6]}, flags={fl(chs[0][2])}, res0={chs[0][6]}")
