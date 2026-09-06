#!/usr/bin/env python3
"""GOLDEN-03 §8 — verify framework attr ids from the EXT-01 APK bytes.

Oracle for the framework attribute constants the runtime style/theme path
consumes. NO constant may be taken from memory: every id below is READ from
the binary AXML resource map / ARSC bag of the frozen fixture.
"""
import struct, sys, zipfile

APK = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/z/corpus/external_hello/HelloWorldSelfAware-1.1.0-android.apk"

z = zipfile.ZipFile(APK)
arsc = z.read("resources.arsc")
layouts = [n for n in z.namelist() if n.startswith("res/") and n.endswith(".xml")]

def u16(b, o): return struct.unpack_from("<H", b, o)[0]
def u32(b, o): return struct.unpack_from("<I", b, o)[0]

def pool_strings(b, sp):
    count = u32(b, sp + 8)
    flags = u32(b, sp + 16)
    sos = u32(b, sp + 20)
    utf8 = bool(flags & 0x100)
    out = []
    for i in range(count):
        p = sp + sos + u32(b, sp + 28 + 4 * i)
        if utf8:
            def varint(q):
                v = b[q]
                return (v, 1) if v < 0x80 else (((b[q] & 0x7F) << 8) | b[q + 1], 2)
            _, n1 = varint(p); bl, n2 = varint(p + n1)
            out.append(b[p+n1+n2:p+n1+n2+bl].decode("utf-8", "replace"))
        else:
            sl = u16(b, p)
            if sl & 0x8000: sl = ((sl & 0x7FFF) << 16) | u16(b, p + 2)
            out.append(b[p+2:p+2+2*sl].decode("utf-16-le", "replace"))
    return out

def walk_chunks(b, start=0):
    off = start
    while off + 8 <= len(b):
        ctype, hsz, csize = u16(b, off), u16(b, off+2), u32(b, off+4)
        if csize < 8: break
        yield off, ctype, hsz, csize
        off += csize

def axml_attr_ids(b):
    """string pool + resource map of a binary AXML chunk stream."""
    ids = {}
    for off, ctype, hsz, csize in walk_chunks(b, 8):
        if ctype == 0x0001:  # string pool
            ids["_strings"] = pool_strings(b, off)
        elif ctype == 0x0180:  # resource map: index i ↔ string i
            strs = ids.get("_strings", [])
            n = (csize - hsz) // 4
            for i in range(min(n, len(strs))):
                ids.setdefault("_map", {})[strs[i]] = u32(b, off + hsz + 4*i)
    return ids.get("_map", {})

print("== EXT-01 layout attribute ids (read from AXML resource maps) ==")
seen = {}
for lname in layouts:
    try:
        seen.update(axml_attr_ids(z.read(lname)))
    except Exception as e:
        print(f"  ({lname}: {e})")
for name in ("textSize", "textColor", "textAppearance", "background", "gravity",
             "padding", "fontFamily", "lineSpacingMultiplier", "elegantTextHeight",
             "text", "layout_width", "layout_height", "hint", "singleLine"):
    print(f"  android:{name} = " +
          (f"0x{seen[name]:08x}" if name in seen else "(not in map)"))

print("\n== EXT-01 ARSC style bags ==")
def style_bags(b):
    for off, ctype, hsz, csize in walk_chunks(b, 0):
        if ctype != 0x0200: continue
        pkg_off = off
        type_strings = pool_strings(b, pkg_off + u32(b, pkg_off + 268))
        key_strings  = pool_strings(b, pkg_off + u32(b, pkg_off + 276))
        pos = pkg_off + hsz
        # skip the two pools right after the package header
        for _ in range(2):
            if pos + 8 <= len(b) and u16(b, pos) == 0x0001:
                pos += u32(b, pos + 4)
        for o2, ct2, h2, cs2 in walk_chunks(b, pos):
            if o2 + cs2 > pkg_off + csize: break
            if ct2 != 0x0201: continue
            type_id = b[o2 + 8]
            entry_count = u32(b, o2 + 12)
            entries_start = u32(b, o2 + 16)
            tname = type_strings[type_id-1] if 0 < type_id <= len(type_strings) else "?"
            if tname != "style": continue
            for i in range(entry_count):
                eo = u32(b, o2 + h2 + 4*i)
                if eo == 0xFFFFFFFF: continue
                ep = o2 + entries_start + eo
                eflags = u16(b, ep + 2)
                if not (eflags & 1): continue
                key_idx = u32(b, ep + 4)
                name = key_strings[key_idx] if key_idx < len(key_strings) else "?"
                parent = u32(b, ep + 8)
                count = u32(b, ep + 12)
                items = []
                m = ep + 16
                for _ in range(count):
                    items.append((u32(b, m), b[m+4+3], u32(b, m+4+4)))
                    m += 20
                yield name, parent, items

for name, parent, items in style_bags(arsc):
    print(f"  style/{name} (parent=0x{parent:08x}):")
    for key, vt, vd in items:
        print(f"    key 0x{key:08x} type=0x{vt:02x} data=0x{vd:08x}")
