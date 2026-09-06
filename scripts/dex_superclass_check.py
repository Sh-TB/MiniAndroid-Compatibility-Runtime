#!/usr/bin/env python3
"""Verify superclass ground truth for a class across all DEX files of an APK."""
import struct, zipfile, sys

def u1(b, o): return b[o]
def u2(b, o): return struct.unpack_from('<H', b, o)[0]
def u4(b, o): return struct.unpack_from('<I', b, o)[0]

def uleb128(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7f) << s; s += 7
        if not (x & 0x80): return r, o

def parse_dex(b):
    string_off = u4(b, 0x38)
    type_off = u4(b, 0x44); type_size = u4(b, 0x40)
    proto_off = u4(b, 0x54)
    field_off = u4(b, 0x64); field_size = u4(b, 0x60)
    method_off = u4(b, 0x74); method_size = u4(b, 0x70)
    class_off = u4(b, 0x64 - 0x10 + 0x10) if False else u4(b, 0x64)
    # class_defs: header offset 0x60 = class_defs_size, 0x64 = class_defs_off
    class_size = u4(b, 0x60); class_off = u4(b, 0x64)

    def getstr(idx):
        off = u4(b, string_off + 4 * idx)
        ln, off = uleb128(b, off)
        return b[off:off + ln].decode('utf-8', 'replace')

    def gettype(idx):
        return getstr(u4(b, type_off + 4 * idx))

    out = {}
    for i in range(class_size):
        o = class_off + 32 * i
        cls_idx = u4(b, o)
        super_idx = u4(b, o + 8)
        try:
            cname = gettype(cls_idx)
            sname = gettype(super_idx) if super_idx != 0xFFFFFFFF else '<none>'
        except Exception:
            continue
        out[cname] = sname
    return out

apk = sys.argv[1]
target = sys.argv[2] if len(sys.argv) > 2 else 'Landroidx/arch/core/executor/ArchTaskExecutor;'
z = zipfile.ZipFile(apk)
for dn in sorted(n for n in z.namelist() if n.endswith('.dex')):
    try:
        classes = parse_dex(z.read(dn))
    except Exception as e:
        print(f"{dn}: PARSE ERROR {e}"); continue
    if target in classes:
        print(f"{dn}: {target} extends {classes[target]}")
    else:
        print(f"{dn}: {target} NOT PRESENT ({len(classes)} classes)")
    # also any OTHER dex defining it would be a duplicate-def conflict
