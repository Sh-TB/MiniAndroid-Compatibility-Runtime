#!/usr/bin/env python3
"""CONT-54: targeted DEX method finder — locate DrawerLayout.getChildMeasureSpec
by walking class_data directly (the cont26 disassembler missed it).

Usage: cont54_find_method.py <apk> <Lclass;> <method-name-substring>
"""
import struct, sys, zipfile

def uleb128(buf, off):
    result = 0; shift = 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7f) << shift
        if (b & 0x80) == 0: break
        shift += 7
    return result, off

class Dex:
    def __init__(self, name, d):
        self.name = name; self.d = d
        (self.string_ids_size, self.string_ids_off,
         self.type_ids_size, self.type_ids_off,
         self.proto_ids_size, self.proto_ids_off,
         self.field_ids_size, self.field_ids_off,
         self.method_ids_size, self.method_ids_off,
         self.class_defs_size, self.class_defs_off) = struct.unpack_from("<12I", d, 56)
    def s(self, idx):
        off = struct.unpack_from("<I", self.d, self.string_ids_off + 4*idx)[0]
        _, o = uleb128(self.d, off)
        end = self.d.index(b"\x00", o)
        return self.d[o:end].decode("utf-8", "replace")
    def t(self, idx):
        si = struct.unpack_from("<I", self.d, self.type_ids_off + 4*idx)[0]
        return self.s(si)
    def mid(self, idx):
        ci, proto = struct.unpack_from("<HH", self.d, self.method_ids_off + 8*idx)
        nm, = struct.unpack_from("<I", self.d, self.method_ids_off + 8*idx + 4)
        return self.t(ci), self.s(nm), self.s(proto)
    def fid(self, idx):
        ci, ty = struct.unpack_from("<HH", self.d, self.field_ids_off + 8*idx)
        nm, = struct.unpack_from("<I", self.d, self.field_ids_off + 8*idx + 4)
        return self.t(ci), self.s(nm), self.t(ty)
    def class_data(self, cls):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + 32*i
            class_idx, access, sup, ifaces, src, ann, cdata, svals = struct.unpack_from("<8I", self.d, off)
            if self.t(class_idx) != cls: continue
            if not cdata: return []
            o = cdata
            sf, o = uleb128(self.d, o)
            inf, o = uleb128(self.d, o)
            dm, o = uleb128(self.d, o)
            vm, o = uleb128(self.d, o)
            out = []
            last = 0
            for _ in range(sf):
                fi, o = uleb128(self.d, o); fi += last; last = fi
                acc, o = uleb128(self.d, o)
                out.append(("static-field", fi, acc, None))
            last = 0
            for _ in range(inf):
                fi, o = uleb128(self.d, o); fi += last; last = fi
                acc, o = uleb128(self.d, o)
                out.append(("instance-field", fi, acc, None))
            last = 0
            for _ in range(dm):
                mi, o = uleb128(self.d, o); mi += last; last = mi
                acc, o = uleb128(self.d, o)
                co, o = uleb128(self.d, o)
                out.append(("direct", mi, acc, co))
            last = 0
            for _ in range(vm):
                mi, o = uleb128(self.d, o); mi += last; last = mi
                acc, o = uleb128(self.d, o)
                co, o = uleb128(self.d, o)
                out.append(("virtual", mi, acc, co))
            return out
        return None

def main():
    apk, cls, sub = sys.argv[1], sys.argv[2], sys.argv[3]
    if apk.endswith(".apk"):
        z = zipfile.ZipFile(apk)
        dexes = [(n, z.read(n)) for n in z.namelist() if n.endswith(".dex")]
    else:
        dexes = [(apk.split("/")[-1], open(apk, "rb").read())]
    for name, d in dexes:
        dx = Dex(name, d)
        items = dx.class_data(cls)
        if items is None:
            continue
        print(f"[{name}] {cls}: {len(items)} members")
        for kind, idx, acc, co in items:
            if kind.endswith("field"):
                c, n, ty = dx.fid(idx)
                print(f"  {kind} f@{idx} {c}.{n} : {ty} acc={acc:#x}")
            else:
                c, n, p = dx.mid(idx)
                mark = "  <<<" if sub.lower() in n.lower() else ""
                print(f"  {kind} m@{idx} {c}.{n} {p} acc={acc:#x} code_off={co}{mark}")

if __name__ == "__main__":
    main()
