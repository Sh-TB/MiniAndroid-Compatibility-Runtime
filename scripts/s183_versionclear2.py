#!/usr/bin/env python3
"""s183_versionclear2.py — properly remove bionic symbol-version requirements:
  1) .dynamic: DELETE DT_VERNEED(0x6ffffffe)/DT_VERNEEDNUM(0x6fffffff) entries by
     shifting the tail left (table stays contiguous, DT_NULL-terminated).
  2) .gnu.version: every dynsym entry -> 1 (unversioned global).
In-place same-size edits only; output file gets a _novers.so suffix."""
import struct, sys

VERNEED, VERNEEDNUM = 0x6FFFFFFE, 0x6FFFFFFF

def clear(path):
    f = bytearray(open(path, "rb").read())
    e_shoff = struct.unpack_from("<Q", f, 0x28)[0]
    e_shentsize = struct.unpack_from("<H", f, 0x3A)[0]
    e_shnum = struct.unpack_from("<H", f, 0x3C)[0]
    e_shstrndx = struct.unpack_from("<H", f, 0x3E)[0]
    secs = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        name, typ, flags, addr, offset, size = struct.unpack_from("<IIQQQQ", f, off)
        secs.append(dict(name_off=name, typ=typ, off=offset, size=size))
    shstr_off = secs[e_shstrndx]["off"]
    def sname(s):
        e = f.index(b"\0", shstr_off + s["name_off"])
        return f[shstr_off + s["name_off"]:e].decode("ascii", "replace")
    dyn = versym = None
    nsym = 0
    for s in secs:
        nm = sname(s)
        if nm == ".dynamic": dyn = s
        if nm == ".gnu.version": versym = s
        if nm == ".dynsym": nsym = s["size"] // 24
    # 1) versym -> 1
    for i in range(nsym):
        struct.pack_into("<H", f, versym["off"] + 2 * i, 1)
    # 2) rebuild .dynamic without VERNEED/VERNEEDNUM
    p = dyn["off"]
    entries = []
    while p < dyn["off"] + dyn["size"]:
        tag, val = struct.unpack_from("<qQ", f, p)
        entries.append((tag, val))
        p += 16
        if tag == 0: break
    kept = [(t, v) for (t, v) in entries if t not in (VERNEED, VERNEEDNUM)]
    dropped = len(entries) - len(kept)
    p = dyn["off"]
    for t, v in kept:
        struct.pack_into("<qQ", f, p, t, v)
        p += 16
    # pad remainder with DT_NULL / 0
    while p < dyn["off"] + dyn["size"]:
        struct.pack_into("<qQ", f, p, 0, 0)
        p += 16
    out = path.replace(".so", "_novers.so") if path.endswith(".so") else path + "_novers"
    open(out, "wb").write(f)
    print(f"{path}: dropped {dropped} verneed entries, versym[{nsym}]->1 => {out}")
    return out

if __name__ == "__main__":
    for p in sys.argv[1:]:
        clear(p)
