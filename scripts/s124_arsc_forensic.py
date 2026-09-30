#!/usr/bin/env python3
"""Robust ARSC chunk walker: top-level + inside the FIRST package chunk only.
Prints every ResTable_type that fails MiniAndroid's entries_start check."""
import struct

path = "/home/z/my-project/miniandroid/framework_res/resources.arsc"
data = open(path, "rb").read()
N = len(data)

def chunk_at(off):
    t, hs, sz = struct.unpack_from("<HHI", data, off)
    return t, hs, sz

t, hs, sz = chunk_at(0)
print(f"table: type=0x{t:04x} header={hs} size={sz} file={N}")

# top-level walk, bounded by the TABLE size
off = hs
pkg = None
top = []
while off + 8 <= min(sz, N):
    t2, h2, s2 = chunk_at(off)
    if s2 < 8 or off + s2 > min(sz, N):
        print(f"[top-walk] stop: bad chunk @0x{off:x} type=0x{t2:04x} size={s2}")
        break
    top.append((hex(off), hex(t2), h2, s2))
    if t2 == 0x0200 and pkg is None:
        pkg = (off, h2, s2)
    off += s2
print("top-level chunks:", top)

if not pkg:
    raise SystemExit("no package chunk")

po, phs, psz = pkg
pid, = struct.unpack_from("<I", data, po + 8)
print(f"package @0x{po:x} hdr={phs} size={psz} id=0x{pid:x}")

off = po + phs
end = po + psz
n_type = n_spec = n_pool = 0
fails = []
while off + 8 <= end:
    t2, h2, s2 = chunk_at(off)
    if s2 < 8 or off + s2 > end:
        print(f"[pkg-walk] stop: bad chunk @0x{off:x} type=0x{t2:04x} size={s2} (end=0x{end:x})")
        break
    if t2 == 0x0001:
        n_pool += 1
    elif t2 == 0x0202:
        n_spec += 1
    elif t2 == 0x0201:
        n_type += 1
        tid = data[off + 8]
        flags = data[off + 9]          # TRUE ResTable_type.flags (id@8, flags@9)
        entry_count, = struct.unpack_from("<I", data, off + 12)
        entries_start, = struct.unpack_from("<I", data, off + 16)
        config_size, = struct.unpack_from("<I", data, off + 20)
        need = h2 + entry_count * (2 if flags & 0x02 else 4)
        if entries_start < need or entries_start > s2:
            fails.append((tid, flags, h2, entry_count, entries_start, s2, need))
    off += s2
print(f"pools={n_pool} type_specs={n_spec} types={n_type}")
from collections import Counter
print("flags byte histogram:", dict(Counter(hex(f) for _, f, *_ in fails) | { }))
print(f"FAILING TYPES: {len(fails)}")
for f in fails[:10]:
    tid, flags, h2, cnt, es, s2, need = f
    print(f"  tid={tid} flags=0x{flags:x} hdrSize={h2} entryCount={cnt} "
          f"entriesStart={es} chunkSize={s2} needed<={need} DELTA={need-es}")
