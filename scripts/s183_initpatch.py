#!/usr/bin/env python3
"""s183_initpatch.py — zero DT_INIT / DT_INIT_ARRAYSZ in an ELF64 .so (defer constructors).
Also prints the original values for disassembly reference."""
import struct, sys

def patch(path):
    f = bytearray(open(path, "rb").read())
    e_shoff = struct.unpack_from("<Q", f, 0x28)[0]
    e_shentsize = struct.unpack_from("<H", f, 0x3A)[0]
    e_shnum = struct.unpack_from("<H", f, 0x3C)[0]
    secs = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        name, typ, flags, addr, offset, size = struct.unpack_from("<IIQQQQ", f, off)
        secs.append((name, typ, offset, size))
    e_shstrndx = struct.unpack_from("<H", f, 0x3E)[0]
    shstr_off = secs[e_shstrndx][2]
    def sname(n):
        e = f.index(b"\0", shstr_off + n)
        return f[shstr_off + n:e].decode("ascii", "replace")
    dyn = None
    for name, typ, off, size in secs:
        if sname(name) == ".dynamic": dyn = (off, size)
    p = dyn[0]
    while p < dyn[0] + dyn[1]:
        tag, val = struct.unpack_from("<qQ", f, p)
        p += 16
        if tag == 0: break
        if tag in (12, 25, 27):  # DT_INIT=12, DT_INIT_ARRAY=25, DT_INIT_ARRAYSZ=27
            print(f"  tag={tag:#x} val={val:#x}")
            if tag in (12, 27):
                struct.pack_into("<Q", f, p - 8, 0)
    out = path.replace(".so", "_noinit.so").replace("_novers", "")
    open(out, "wb").write(f)
    print(f"=> {out}")
    return out

for p in sys.argv[1:]:
    patch(p)
