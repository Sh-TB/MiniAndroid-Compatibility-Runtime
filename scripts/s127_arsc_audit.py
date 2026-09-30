#!/usr/bin/env python3
"""S127 — R-NEW-423 ground-truth audit.

Independent (Python) minimal ARSC walker that dumps the RAW byte-level truth
for the resources that R-NEW-423 reports as corrupted by the C++ parser:
  0x0106000e background_dark     (color  , truth #ff000000)
  0x0106000f background_light    (color  , truth #ffffffff)
  0x01080098 screen_background_dark   (drawable)
  0x01080099 screen_background_light  (drawable)
plus the theme bag 0x01030237 (Theme.Material.Light) windowBackground item.

Output: per (type_id, bucket) chunk header law fields + raw Res_value bytes
at the computed entry positions, per AOSP ResourceTypes.h encoding laws.
"""
import struct, sys

ARSC = "miniandroid/framework_res/resources.arsc"

def rd16(b, o): return struct.unpack_from("<H", b, o)[0]
def rd32(b, o): return struct.unpack_from("<I", b, o)[0]

def parse_string_pool(b, off):
    ctype, hsize, size = struct.unpack_from("<HHI", b, off)
    assert ctype == 0x0001, hex(ctype)
    strcount, stylecount, flags, strstart, stylestart = struct.unpack_from("<IIIII", b, off + 8)
    utf8 = bool(flags & 0x100)
    strs = []
    base = off + strstart
    for i in range(strcount):
        p = base + rd32(b, off + 20 + 4 * i)
        if utf8:
            # u16len (1-2 bytes), u8len (1-2 bytes), data
            n = b[p]; p += 1
            if n & 0x80: n = ((n & 0x7F) << 8) | b[p]; p += 1
            ln = b[p]; p += 1
            if ln & 0x80: ln = ((ln & 0x7F) << 8) | b[p]; p += 1
            strs.append(b[p:p + ln].decode("utf-8", "replace"))
        else:
            n = struct.unpack_from("<H", b, p)[0]; p += 2
            if n & 0x8000:
                n2 = struct.unpack_from("<H", b, p)[0]; p += 2
                n = ((n & 0x7FFF) << 16) | n2
            strs.append(b[p:p + 2 * n].decode("utf-16-le", "replace"))
    return strs, size

def config_desc(b, off, size):
    lang = b[off + 8:off + 10]; country = b[off + 10:off + 12]
    parts = []
    if lang.strip(b"\x00"): parts.append(lang.decode("latin1"))
    if country.strip(b"\x00"): parts.append("-r" + country.decode("latin1"))
    density = b[off + 14]
    if density: parts.append(f"{65535 if density==0xFF else density}dpi")
    night = b[off + 21] if size >= 22 else 0   # screenLayout: night bits 4-5? (layoutDir..)
    # ResTable_config: orientation@12 touchscreen@13 density@14 keyboard@15 nav@16 inputFlags@17
    # screenWidth@18 screenHeight@20 sdkVersion@26 screenLayout@28 uiMode@29 (uiModeNight bit=0x20)
    if size >= 30:
        uimode = b[off + 29]
        if uimode & 0x20: parts.append("night")
        elif uimode & 0x10: parts.append("notnight")
    return "-".join(parts) if parts else "(default)"

def main():
    d = open(ARSC, "rb").read()
    print(f"table size {len(d)}")
    t, hs, size = struct.unpack_from("<HHI", d, 0)
    pkg_count = rd32(d, 8)
    print(f"RES_TABLE type=0x{t:04x} headerSize={hs} size={size} packages={pkg_count}")
    gstrs, gsize = parse_string_pool(d, hs)
    print(f"global pool strings={len(gstrs)} chunkSize={gsize}")

    pos = hs + gsize
    targets = {0x06: [0x0E, 0x0F], 0x08: [0x98, 0x99]}
    bag_id, bag_attr = 0x01030237, 0x01010054
    bag_target = {0x01: [bag_id & 0xFFFF]}          # style 0x01030237 entry index
    entries = {}   # resid -> list of (config, rawval_desc)
    bag_items = None

    while pos + 8 <= size:
        ctype, chs, csize = struct.unpack_from("<HHI", d, pos)
        if csize == 0: break
        if ctype == 0x0200:  # package
            pkg_id = rd32(d, pos + 8)
            tstr_off = rd32(d, pos + 268)
            kstr_off = rd32(d, pos + 276)
            print(f"\nPACKAGE id=0x{pkg_id:02x} at {pos} tstr={tstr_off} kstr={kstr_off} size={csize}")
            tstrs, _ = parse_string_pool(d, pos + tstr_off)
            kstrs, _ = parse_string_pool(d, pos + kstr_off)
            ipos = pos + chs
            if tstr_off and ipos == pos + tstr_off:
                _, ts = parse_string_pool(d, ipos); ipos += ts
            if kstr_off and ipos == pos + kstr_off:
                _, ks = parse_string_pool(d, ipos); ipos += ks
            while ipos + 8 <= pos + csize:
                itype, ihs, isize = struct.unpack_from("<HHI", d, ipos)
                if isize == 0: break
                if itype == 0x0201:  # type chunk (0x0202 = typeSpec, skipped)
                    tid = d[ipos + 8]
                    flags = d[ipos + 9]
                    ecnt = rd32(d, ipos + 12)
                    estart = rd32(d, ipos + 16)
                    csize2 = rd32(d, ipos + 20)
                    cfg = config_desc(d, ipos + 20, csize2)
                    sparse = flags & 0x01; off16 = flags & 0x02
                    want = None
                    if tid in targets: want = targets[tid]
                    elif tid == 0x01 and (bag_id & 0xFFFF) < ecnt: want = bag_target[0x01]
                    if want is not None:
                        print(f"\n TYPE {tid} ('{tstrs[tid-1] if tid-1 < len(tstrs) else '?'}') "
                              f"cfg='{cfg}' flags=0x{flags:02x} sparse={sparse} off16={off16} "
                              f"ecnt={ecnt} estart={estart} hdr={chs} csize2={csize2} @chunk{ipos}")
                        enc = "SPARSE" if sparse else ("OFF16" if off16 else "DENSE")
                        offarr = ipos + ihs
                        posmap = {}
                        if sparse:
                            for i in range(ecnt):
                                idx, of = struct.unpack_from("<HH", d, offarr + 4 * i)
                                if idx in want: posmap[idx] = estart + (of << 2)
                        elif off16:
                            for i in range(ecnt):
                                o = rd16(d, offarr + 2 * i)
                                if i in want and o != 0xFFFF: posmap[i] = estart + (o << 2)
                        else:
                            for i in range(ecnt):
                                o = rd32(d, offarr + 4 * i)
                                if i in want and o != 0xFFFFFFFF: posmap[i] = estart + o
                        for idx in want:
                            if idx not in posmap:
                                print(f"   entry 0x{idx:04x}: NO_ENTRY")
                                continue
                            ep = ipos + posmap[idx]
                            esz, efl = struct.unpack_from("<HH", d, ep)
                            kidx = rd32(d, ep + 4)
                            name = kstrs[kidx] if kidx < len(kstrs) else "?"
                            rname = f"{tstrs[tid-1]}/{name}"
                            resid = (pkg_id << 24) | (tid << 16) | idx
                            if efl & 0x01:  # complex
                                parent = rd32(d, ep + 8)
                                cnt = rd32(d, ep + 12)
                                print(f"   entry 0x{idx:04x} {rname}: COMPLEX parent=0x{parent:08x} count={cnt} @abs{ep}")
                                mp = ep + 16
                                items = []
                                for mi in range(cnt):
                                    mkey = rd32(d, mp)
                                    vsz, vr0, vty = struct.unpack_from("<HBB", d, mp + 4)
                                    vdata = rd32(d, mp + 8)
                                    sval = gstrs[vdata] if vty == 0x03 and vdata < len(gstrs) else ""
                                    print(f"      key=0x{mkey:08x} type=0x{vty:02x} data=0x{vdata:08x} {sval!r}")
                                    if mkey == bag_attr: items = (mkey, vty, vdata)
                                    mp += 12
                                if tid == 0x01 and idx == (bag_id & 0xFFFF):
                                    bag_items = (resid, parent, items)
                            else:
                                vsz, vr0, vty = struct.unpack_from("<HBB", d, ep + esz)
                                vdata = rd32(d, ep + esz + 4)
                                sval = gstrs[vdata] if vty == 0x03 and vdata < len(gstrs) else ""
                                print(f"   entry 0x{idx:04x} {rname}: type=0x{vty:02x}({vty}) data=0x{vdata:08x} "
                                      f"{sval!r} esz={esz} rawbytes={d[ep+esz:ep+esz+8].hex()}")
                                entries.setdefault(resid, []).append((cfg, vty, vdata))
                    elif tid in (6, 8):
                        pass
                ipos += isize
        pos += csize

    print("\n=== TRUTH SUMMARY (Python instrument) ===")
    for rid in (0x0106000e, 0x0106000f, 0x01080098, 0x01080099):
        rows = entries.get(rid, [])
        print(f"0x{rid:08x}: {len(rows)} buckets")
        for cfg, vty, vdata in rows:
            print(f"   cfg={cfg}: type=0x{vty:02x} data=0x{vdata:08x}")
    if bag_items:
        rid, parent, items = bag_items
        print(f"\nbag 0x{rid:08x}: parent=0x{parent:08x} windowBackground item={items}")

if __name__ == "__main__":
    main()
