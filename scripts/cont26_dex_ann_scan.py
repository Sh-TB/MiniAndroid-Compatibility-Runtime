#!/usr/bin/env python3
"""CONT-26: minimal DEX class-annotation scanner.

Answers ONE question: does the DEX class_def for a given class carry a
runtime-visible annotations_directory_item with a class annotation set,
and what annotation types/elements are decoded there?

Usage: cont26_dex_ann_scan.py <file.apk-or-.dex> <class-desc-suffix>...
"""
import struct, sys, zipfile, io

def uleb128(buf, off):
    result = 0; shift = 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7f) << shift
        if (b & 0x80) == 0: break
        shift += 7
    return result, off

def load_dexes(path):
    if path.endswith(".apk"):
        z = zipfile.ZipFile(path)
        return [(n, z.read(n)) for n in z.namelist() if n.endswith(".dex")]
    return [(path.split("/")[-1], open(path, "rb").read())]

class Dex:
    def __init__(self, name, d):
        self.name = name; self.d = d
        (self.string_ids_size, self.string_ids_off,
         self.type_ids_size, self.type_ids_off,
         _, _,
         _, _,
         _, _,
         self.class_defs_size, self.class_defs_off) = struct.unpack_from("<12I", d, 56)
    def s(self, idx):
        off = struct.unpack_from("<I", self.d, self.string_ids_off + 4*idx)[0]
        _, o = uleb128(self.d, off)
        end = self.d.index(b"\x00", o)
        return self.d[o:end].decode("utf-8", "replace")
    def t(self, idx):
        if idx >= self.type_ids_size: return "?"
        si = struct.unpack_from("<I", self.d, self.type_ids_off + 4*idx)[0]
        return self.s(si)
    def class_def(self, name):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + 32*i
            class_idx, access, sup, ifaces, src, ann, cdata, svals = struct.unpack_from("<8I", self.d, off)
            if self.t(class_idx) == name:
                return {"access": access, "annotations_off": ann, "idx": i}
        return None
    def annotations_dir(self, off):
        d = self.d
        class_ann_off, fields, methods, params = struct.unpack_from("<4I", d, off)
        out = {"class_annotations_off": class_ann_off, "n_fields": fields,
               "n_methods": methods, "n_params": params, "class_anns": []}
        if class_ann_off:
            n = struct.unpack_from("<I", d, class_ann_off)[0]
            for k in range(n):
                eoff = struct.unpack_from("<I", d, class_ann_off + 4 + 4*k)[0]
                vis = d[eoff]
                # encoded_annotation: type_idx uleb, size uleb, elements
                o = eoff + 1
                type_idx, o = uleb128(d, o)
                sz, o = uleb128(d, o)
                elems = []
                for _ in range(sz):
                    name_idx, o = uleb128(d, o)
                    val = self._enc_value(d, o)
                    o = val[1]
                    elems.append((self.s(name_idx), val[0]))
                out["class_anns"].append({"visibility": vis, "type": self.t(type_idx), "elements": elems})
        return out
    def _enc_value(self, d, o):
        # returns (desc, next_off) — conservative decode
        b = d[o]; arg = (b >> 5) & 7; vtype = b & 0x1f; o2 = o + 1
        size = arg + 1
        if vtype == 0x1c:  # array
            n, o3 = uleb128(d, o2)
            for _ in range(n):
                _, o3 = self._enc_value(d, o3)
            return ("array[%d]" % n, o3)
        if vtype == 0x1d or vtype == 0x1e or vtype == 0x1f:
            return ("opaque", o2)  # nested ann/enum/method/field: encoded differently, stop here
        if vtype == 0x17:  # string
            idx = int.from_bytes(d[o2:o2+size], "little")
            return (repr(self.s(idx)), o2 + size)
        if vtype == 0x18:  # type
            idx = int.from_bytes(d[o2:o2+size], "little")
            return (self.t(idx), o2 + size)
        return ("val:type=0x%x" % vtype, o2 + size)

def main():
    path = sys.argv[1]
    wanted = sys.argv[2:]
    for name, data in load_dexes(path):
        dx = Dex(name, data)
        for w in wanted:
            cd = dx.class_def(w)
            if cd is None: continue
            print(f"[{name}] {w} class_def idx={cd['idx']} annotations_off=0x{cd['annotations_off']:x}")
            if cd["annotations_off"]:
                ad = dx.annotations_dir(cd["annotations_off"])
                print(f"  dir: class_anns_off=0x{ad['class_annotations_off']:x} fields={ad['n_fields']} methods={ad['n_methods']} params={ad['n_params']}")
                for a in ad["class_anns"]:
                    print(f"  ANN vis={a['visibility']} type={a['type']} elements={a['elements']}")
            else:
                print("  NO annotations_directory_item")

if __name__ == "__main__":
    main()
