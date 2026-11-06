#!/usr/bin/env python3
"""s183_dt_needed.py — read DT_NEEDED of extracted Android .so files to scope the B1 law
(bionic->host dependency mapping needed for host dlopen)."""
import struct, sys

def dt_needed(path):
    f = open(path, "rb").read()
    if f[:4] != b"\x7fELF":
        return ["NOT_ELF"]
    ei_class = f[4]
    if ei_class != 2:  # 64-bit only here
        return ["ELF32-unsupported"]
    e_shoff = struct.unpack_from("<Q", f, 0x28)[0]
    e_shentsize = struct.unpack_from("<H", f, 0x3A)[0]
    e_shnum = struct.unpack_from("<H", f, 0x3C)[0]
    secs = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        name, typ, flags, addr, offset, size = struct.unpack_from("<IIQQQQ", f, off)
        secs.append((name, typ, offset, size))
    def sname(n):
        # shstrtab: find section of type SHT_STRTAB whose range covers n —
        # safest: use the section header's own string table via e_shstrndx
        return None
    # use section[0]'s sh_link chain: simpler — parse with shstrtab index from header
    e_shstrndx = struct.unpack_from("<H", f, 0x3E)[0]
    shstr_off = secs[e_shstrndx][2]
    def sname2(n):
        e = f.index(b"\0", shstr_off + n)
        return f[shstr_off + n:e].decode("ascii", "replace")
    dyn = strtab = None
    for name, typ, off, size in secs:
        nm = sname2(name)
        if nm == ".dynamic": dyn = (off, size)
        if nm == ".dynstr": strtab = (off, size)
    if not dyn or not strtab:
        return ["no .dynamic/.dynstr"]
    needed, soname = [], None
    p = dyn[0]
    while p < dyn[0] + dyn[1]:
        tag, val = struct.unpack_from("<qQ", f, p)
        p += 16
        if tag == 0: break
        if tag == 1:
            e = f.index(b"\0", strtab[0] + val)
            needed.append(f[strtab[0] + val:e].decode("ascii", "replace"))
        if tag == 14:  # DT_SONAME
            e = f.index(b"\0", strtab[0] + val)
            soname = f[strtab[0] + val:e].decode("ascii", "replace")
    return needed, soname

for path in sys.argv[1:]:
    try:
        n, so = dt_needed(path)
        print(f"{path.split('/')[-1]}: SONAME={so} DT_NEEDED={n}")
    except Exception as e:
        print(f"{path}: ERROR {e}")
