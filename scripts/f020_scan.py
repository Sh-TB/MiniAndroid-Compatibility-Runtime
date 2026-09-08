#!/usr/bin/env python3
"""f020_scan.py — bulk DEX scanner for F-020 forensics.

Greps ALL classes of a multi-dex APK for:
  - static field refs (sget/sput) matching  <class>.<field>
  - invoke-direct <init> of a class         (construction sites)
  - invoke-* of a specific method           <class>.<name>

Prints: <kind> <class>.<method> pc=0xNN -> <target>
"""
import sys, zipfile, struct

RE = "/home/z/my-project/MiniAndroid-Compatibility-Runtime/scripts/m3_disasm.py"
spec = __import__("importlib.util", fromlist=["util"]).spec_from_file_location("m3dis", RE)
m3 = __import__("importlib.util", fromlist=["util"]).module_from_spec(spec)
spec.loader.exec_module(m3)

def main():
    apk, target, kind = sys.argv[1], sys.argv[2], sys.argv[3]  # kind: field|ctor|invoke
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
        proto_off = u4(d, 0x4C)
        f_off = u4(d, 0x54)
        m_off, m_sz = u4(d, 0x5C), u4(d, 0x58)
        c_off, c_sz = u4(d, 0x64), u4(d, 0x60)

        def get_str(i):
            if i >= s_sz: return "<bad>"
            off = u4(d, str_off + 4 * i)
            r, p = uleb(d, off)
            return d[p:p + r].split(b"\x00")[0].decode("utf-8", "replace")

        def type_of(i):
            if i >= t_sz: return "<bad_t>"
            return get_str(u4(d, type_off + 4 * i))

        def field_of2(i):
            fo = f_off + 8 * i
            return f"{type_of(u2(d, fo))}.{get_str(u4(d, fo + 4))}"

        def meth_of2(i):
            mo = m_off + 8 * i
            cls = type_of(u2(d, mo)); name = get_str(u4(d, mo + 4))
            po = proto_off + 12 * u2(d, mo + 2)
            ret = type_of(u2(d, po + 4))
            po_params = u4(d, po + 8)
            params = []
            if po_params:
                pn = u4(d, po_params)
                for k in range(pn):
                    params.append(type_of(u2(d, po_params + 4 + 2 * k)))
            return f"{cls}.{name}({', '.join(params)}){ret}"

        type_of2 = type_of

        for ci in range(c_sz):
            coff = c_off + 32 * ci
            cls_name = type_of(u2(d, coff))
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
                r, p = uleb(d, p)
            idx = 0
            for _ in range(ifn):
                r, p = uleb(d, p); idx += r
                r, p = uleb(d, p)
            for mkind, n in (("direct", dmn), ("virtual", vmn)):
                midx = 0
                for _ in range(n):
                    r, p = uleb(d, p); midx += r
                    r, p = uleb(d, p)
                    r, p = uleb(d, p); code_off = r
                    if not code_off: continue
                    mth = get_str(u4(d, m_off + 8 * midx + 4))
                    insns_size = u2(d, code_off + 12) * 2
                    for (pc, text) in m3.disasm(d, get_str, type_of2, field_of2, meth_of2,
                                                code_off, insns_size):
                        hit = False
                        if kind == "field" and ("sget" in text or "sput" in text):
                            if target in text: hit = True
                        elif kind == "ctor" and "invoke-direct" in text:
                            if target in text and "<init>" in text: hit = True
                        elif kind == "invoke" and "invoke" in text:
                            if target in text: hit = True
                        if hit:
                            print(f"[{dexname}] {kind}: {cls_name}.{mth} pc=0x{pc:x} {text.strip()}")

if __name__ == "__main__":
    main()
