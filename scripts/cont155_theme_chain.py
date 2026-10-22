#!/usr/bin/env python3
"""cont155_theme_chain.py — probe the todolist arsc style parent chain:
does Theme.AppCompat.Empty (the appcompat base) appear, and does any chain
level carry android:windowActionBar (0x10100ab)? Minimal ResTable walk:
type 0x12 (style) chunks, parse ResTable_map_entry bags for a bounded chain.
"""
import struct, sys

APK = sys.argv[1] if len(sys.argv) > 1 else 'upload/fdroid_batch/org.secuso.privacyfriendlytodolist_103.apk'
import zipfile
data = zipfile.ZipFile(APK).read('resources.arsc')

def u16(o): return struct.unpack_from('<H', data, o)[0]
def u32(o): return struct.unpack_from('<I', data, o)[0]

# header
pkg_count = u32(8)
off = u32(0x3C)  # package chunk usually right after table header
# walk top-level for package chunk 0x0200
off = u16(4) if u16(4) > 12 else 12
pkgs = []
p = u16(2)  # header size
while p + 8 <= len(data):
    t, hs, sz = struct.unpack_from('<HHI', data, p)
    if t == 0x0200:
        pkgs.append((p, sz)); break
    p += sz
if not pkgs:
    print('NO PACKAGE CHUNK'); sys.exit(1)
po, psz = pkgs[0]
pkg_id = u32(po+8)
# ResTable_package: type(2) hs(2) size(4) id(4) name(256) typeStrings(+268)
# lastPublicType(+272) keyStrings(+276) lastPublicKey(+280)
print(f'package id=0x{pkg_id:02x} hs={u16(po+2)}')

# walk type chunks inside package (package header = u16(po+2))
styles = {}   # resid -> (bag_parent, keycount, keys)
p = po + u16(po+2)
while p < po + psz:
    t, hs, sz = struct.unpack_from('<HHI', data, p)
    if t == 0x0202:  # type SPEC — skip (RES_TABLE_TYPE_SPEC_TYPE)
        p += sz; continue
    if t == 0x0201:  # ResTable_type — the entries chunk
        tid = data[p+8]
        tflags = data[p+9]
        entry_count = u32(p+12)
        entries_start = u32(p+16)
        if entry_count > 100000 or entries_start > sz:
            p += sz; continue   # implausible chunk — skip (walker hardening)
        base = p
        esz = 2 if (tflags & 0x02) else 4  # SPARSE law: u16 offsets when flag 0x2
        fmt = '<H' if esz == 2 else '<I'
        for ei in range(entry_count):
            eo = struct.unpack_from(fmt, data, p + hs + ei*esz)[0]
            if eo == 0xFFFFFFFF: continue
            eoff = base + entries_start + eo
            esize = u16(eoff)
            flags = u16(eoff+2)
            key_idx = u32(eoff+4)
            if flags & 0x0001:  # complex (bag)
                parent = u32(eoff+8)
                count = u32(eoff+12)
                keys = []
                ok = True
                for i in range(min(count, 600)):
                    ko = eoff + 20 + i*8
                    if ko + 8 > len(data): ok = False; break
                    keys.append(u32(ko))
                resid = (pkg_id << 24) | (tid << 16) | ei
                styles[resid] = (parent, count, keys)
        p += sz; continue
    p += sz

# todolist app theme = 0x7f1201e9; walk parents
cur = 0x7f1201e9
seen = set()
levels = 0
WAB = 0x10100ab
found_wab_at = None
total_keys = 0
while cur and cur not in seen and levels <= 30:
    seen.add(cur)
    ent = styles.get(cur)
    if ent is None:
        print(f'level {levels}: resid 0x{cur:08x} NOT-A-BAG (simple/absent)')
        break
    parent, cnt, keys = ent
    total_keys += cnt
    has_wab = WAB in keys
    if has_wab and found_wab_at is None: found_wab_at = levels
    print(f'level {levels}: resid 0x{cur:08x} parent=0x{parent:08x} keys={cnt} windowActionBar={has_wab}')
    if parent == 0 or parent == cur: break
    cur = parent
    levels += 1
print(f'chain levels={levels} total_keys={total_keys} windowActionBar first at level {found_wab_at}')
