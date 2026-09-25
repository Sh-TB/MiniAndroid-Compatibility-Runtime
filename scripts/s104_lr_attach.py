#!/usr/bin/env python3
"""S104 NEXT-ACTION: disassemble Lr;.onAttachedToWindow (dooz) — find the
Handler field producer that yields null for postAtFrontOfQueue."""
import struct, zipfile

def parse(apk, target):
    zf = zipfile.ZipFile(apk)
    for dexname in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
        d = zf.read(dexname)
        def u4(b, o): return struct.unpack_from("<I", b, o)[0]
        def u2(b, o): return struct.unpack_from("<H", b, o)[0]
        def uleb(b, o):
            r = 0; s = 0
            while True:
                x = b[o]; o += 1
                r |= (x & 0x7f) << s; s += 7
                if not (x & 0x80): break
            return r, o
        string_off = u4(d, 0x3c); type_off = u4(d, 0x44)
        field_off = u4(d, 0x54); method_off = u4(d, 0x5c)
        class_off = u4(d, 0x64); class_defs = u4(d, 0x60)
        def get_str(idx):
            off = u4(d, string_off + idx * 4)
            n, o = uleb(d, off); end = o
            while d[end] != 0: end += 1
            return d[o:end].decode("utf-8", errors="replace")
        def get_type(i): return get_str(u4(d, type_off + i * 4))
        def get_field(idx):
            return f"{get_type(u2(d, field_off+idx*8))}.{get_str(u4(d, field_off+idx*8+4))}"
        def get_m(idx):
            return f"{get_type(u2(d, method_off+idx*8))}->{get_str(u4(d, method_off+idx*8+4))}"
        for ci in range(class_defs):
            coff = class_off + ci * 32
            if get_type(u4(d, coff)) != target: continue
            cdo = u4(d, coff + 24); o = cdo
            sf, o = uleb(d, o); inf, o = uleb(d, o); dm, o = uleb(d, o); vm, o = uleb(d, o)
            print(f"=== {target} in {dexname}: sf={sf} inf={inf} dm={dm} vm={vm}")
            fidx = 0
            for _ in range(sf + inf):
                di, o = uleb(d, o); _, o = uleb(d, o); fidx += di
                print(f"  field: {get_field(fidx)}")
            for sec, cnt in (("D", dm), ("V", vm)):
                midx = 0
                for i in range(cnt):
                    di, o = uleb(d, o); acc, o = uleb(d, o); midx += di
                    name = get_str(u4(d, method_off + midx * 8 + 4))
                    co, o = uleb(d, o); midx += 1
                    if name != "onAttachedToWindow":
                        continue
                    insns_size = u4(d, co + 12)
                    insns_off = co + 16
                    blob = d[insns_off:insns_off + insns_size * 2]
                    print(f"  --- onAttachedToWindow ({sec}) insns={insns_size}")
                    cu = 0
                    while cu < insns_size:
                        w = u2(blob, cu * 2); op = blob[cu * 2]
                        line = f"    u{cu:3d} w={w:#06x} op={op:#04x}"
                        if op == 0x54 or op == 0x5b:
                            fi = u2(blob, cu*2+2)
                            line += f" iget/iput {get_field(fi)}"
                        elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
                            mi = u2(blob, cu*2+2)
                            line += f" invoke {get_m(mi)}"
                        elif op == 0x22:
                            ti = u2(blob, cu*2+2)
                            line += f" new-instance {get_type(ti)}"
                        print(line)
                        cu += 1
                    return
parse("/home/z/my-project/run/s99/apks/io.github.yamin8000.dooz.apk", "Lr;")
