#!/usr/bin/env python3
"""f020_fields.py — list declared instance/static fields of DEX classes."""
import sys, zipfile, struct

apk = sys.argv[1]
classes = sys.argv[2:]
z = zipfile.ZipFile(apk)
dexes = [n for n in z.namelist() if n.startswith("classes") and n.endswith(".dex")]
for dexname in dexes:
    d = z.read(dexname)
    u2 = lambda d, o: struct.unpack_from("<H", d, o)[0]
    u4 = lambda d, o: struct.unpack_from("<I", d, o)[0]
    def uleb(d, p):
        r, s = 0, 0
        while True:
            b = d[p + s]; r |= (b & 0x7F) << (7 * s); s += 1
            if not (b & 0x80): return r, p + s
    str_off, s_sz = u4(d, 0x3C), u4(d, 0x38)
    type_off, t_sz = u4(d, 0x44), u4(d, 0x40)
    f_off, f_sz = u4(d, 0x54), u4(d, 0x50)
    c_off, c_sz = u4(d, 0x64), u4(d, 0x60)

    def get_str(i):
        if i >= s_sz: return "<bad>"
        off = u4(d, str_off + 4 * i)
        r, p = uleb(d, off)
        return d[p:p + r].split(b"\x00")[0].decode("utf-8", "replace")

    def type_of(i):
        if i >= t_sz: return "<bad_t>"
        return get_str(u4(d, type_off + 4 * i))

    def field_of(i):
        fo = f_off + 8 * i
        return f"{type_of(u2(d, fo))}.{get_str(u4(d, fo + 4))} : {type_of(u2(d, fo + 2))}"

    for ci in range(c_sz):
        coff = c_off + 32 * ci
        cls_name = type_of(u2(d, coff))
        if cls_name not in classes: continue
        super_name = type_of(u2(d, coff + 4))
        print(f"CLASS {cls_name} extends {super_name} [{dexname}]")
        acc = u4(d, coff + 8)
        ifc_off = u4(d, coff + 16)
        if ifc_off and ifc_off + 4 <= len(d) - 4:
            n = u4(d, ifc_off)
            if n > 0 and ifc_off + 4 + 2 * n <= len(d):
                print("  implements:", ", ".join(type_of(u2(d, ifc_off + 4 + 2*k)) for k in range(n)))
        cdo = u4(d, coff + 24)
        if not cdo: continue
        p = cdo
        r, p = uleb(d, p); sfn = r
        r, p = uleb(d, p); ifn = r
        r, p = uleb(d, p); dmn = r
        r, p = uleb(d, p); vmn = r
        idx = 0
        for _ in range(sfn):
            r, p = uleb(d, p); idx += r
            r2, p = uleb(d, p); acc2 = r2
            print(f"  static  {field_of(idx)}  acc=0x{acc2:x}")
        idx = 0
        for _ in range(ifn):
            r, p = uleb(d, p); idx += r
            r2, p = uleb(d, p); acc2 = r2
            print(f"  inst    {field_of(idx)}  acc=0x{acc2:x}")
        # method count summary
        print(f"  ({dmn} direct, {vmn} virtual methods)")
