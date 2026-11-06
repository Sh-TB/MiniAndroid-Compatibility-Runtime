#!/usr/bin/env python3
"""s183_versionclear.py — clear bionic symbol-version requirements from an Android .so
so host glibc dlopen binds unversioned. Surgery:
  1) .dynamic: DT_VERNEED=0, DT_VERNEEDNUM=0
  2) .gnu.version (SHT_GNU_versym): set every dynsym entry to 1 (VER_NDX_GLOBAL, unversioned)
Appends nothing; edits in place (versym entries are 2 bytes each, DT values 8 bytes)."""
import struct, sys

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
        secs.append(dict(name_off=name, typ=typ, off=offset, size=size, hdr=off))
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
        if nm == ".dynsym":
            nsym = s["size"] // 24
    assert dyn and versym, "missing .dynamic/.gnu.version"
    # 1) versym all -> 1
    p = versym["off"]
    for i in range(nsym):
        struct.pack_into("<H", f, p + 2 * i, 1)
    # 2) DT_VERNEED (0x6ffffffe) / DT_VERNEEDNUM (0x6fffffff) -> 0
    p = dyn["off"]; cleared = []
    while p < dyn["off"] + dyn["size"]:
        tag, val = struct.unpack_from("<qQ", f, p)
        if tag == 0: break
        if tag in (0x6FFFFFFE, 0x6FFFFFFF):
            struct.pack_into("<Q", f, p + 8, 0)
            cleared.append(hex(tag))
        p += 16
    out = path.replace(".so", "_novers.so")
    open(out, "wb").write(f)
    print(f"cleared {cleared} versym[{nsym}]->1 => {out}")
    return out

if __name__ == "__main__":
    for p in sys.argv[1:]:
        clear(p)
