#!/usr/bin/env python3
"""S175: parse android.jar R$color.class fields (name -> ConstantValue id) without javap.
Class-file format: JVMS §4. Minimal reader for constant pool + fields + ConstantValue."""
import struct, sys, zipfile

def read_u1(b, o): return b[o], o + 1
def read_u2(b, o): return struct.unpack_from(">H", b, o)[0], o + 2
def read_u4(b, o): return struct.unpack_from(">I", b, o)[0], o + 4

def parse_rcolor(class_bytes):
    b = class_bytes
    o = 8  # skip magic(4)+minor(2)+major(2)
    cp_count, o = read_u2(b, o)
    cp = [None] * cp_count  # 1-indexed
    i = 1
    while i < cp_count:
        tag = b[o]; o += 1
        if tag == 1:  # Utf8
            ln, o = read_u2(b, o); cp[i] = ("utf8", b[o:o+ln].decode("utf-8", "replace")); o += ln
        elif tag == 3:  # Integer
            v, o = read_u4(b, o); cp[i] = ("int", v)
        elif tag == 4:  # Float
            v, o = read_u4(b, o); cp[i] = ("float", v)
        elif tag == 5:  # Long
            v, o = read_u4(b, o); cp[i] = ("long", v); i += 1  # 8 bytes + two slots
            v2, o = read_u4(b, o)
        elif tag == 6:  # Double
            o += 8; i += 1
        elif tag == 7:  # Class
            idx, o = read_u2(b, o); cp[i] = ("class", idx)
        elif tag == 8:  # String
            idx, o = read_u2(b, o); cp[i] = ("string", idx)
        elif tag in (9, 10, 11):  # Field/Method/InterfaceMethod ref
            a, o = read_u2(b, o); n, o = read_u2(b, o); cp[i] = ("ref", a, n)
        elif tag == 12:  # NameAndType
            a, o = read_u2(b, o); n, o = read_u2(b, o); cp[i] = ("nat", a, n)
        elif tag == 15:  # MethodHandle
            o += 3
        elif tag == 16:  # MethodType
            o += 2
        elif tag == 17:  # Dynamic
            o += 4
        elif tag == 18:  # InvokeDynamic
            o += 4
        elif tag == 19:  # Module
            o += 2
        elif tag == 20:  # Package
            o += 2
        else:
            raise ValueError(f"unknown cp tag {tag} at {o-1}")
        i += 1
    utf8 = lambda idx: cp[idx][1]
    # access_flags, this_class, super_class
    _, o = read_u2(b, o); _, o = read_u2(b, o); _, o = read_u2(b, o)
    # interfaces
    ic, o = read_u2(b, o); o += 2 * ic
    # fields
    fc, o = read_u2(b, o)
    out = {}
    for _ in range(fc):
        acc, o = read_u2(b, o)
        name_i, o = read_u2(b, o)
        desc_i, o = read_u2(b, o)
        at_count, o = read_u2(b, o)
        const_val = None
        for _ in range(at_count):
            an_i, o = read_u2(b, o)
            alen, o = read_u4(b, o)
            aname = utf8(an_i)
            if aname == "ConstantValue" and alen == 2:
                cv_i, o = read_u2(b, o)
                const_val = cp[cv_i][1] if cp[cv_i][0] == "int" else None
            else:
                o += alen
        if utf8(desc_i) == "I" and const_val is not None:
            out[utf8(name_i)] = const_val
    return out

if __name__ == "__main__":
    jar, inner = sys.argv[1], sys.argv[2]
    with zipfile.ZipFile(jar) as z:
        data = z.read(inner)
    fields = parse_rcolor(data)
    print(f"# {inner}: {len(fields)} int fields with ConstantValue", file=sys.stderr)
    for name in sorted(fields):
        print(f"{name} 0x{fields[name]:08x}")
