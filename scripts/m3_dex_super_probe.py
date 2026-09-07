#!/usr/bin/env python3
"""m3_dex_super_probe.py — DEX ground truth: class_def superclass table."""
import struct, sys, zipfile

def uleb(buf, off):
    result = 0; shift = 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return result, off

def string_at(buf, string_ids_off, idx, hdr):
    off = struct.unpack_from('<I', buf, string_ids_off + idx*4)[0]
    n, p = uleb(buf, off)
    out = bytearray()
    while buf[p] != 0:
        out.append(buf[p]); p += 1
    return out.decode('utf-8', 'replace')

def main(apk, dpath='classes.dex'):
    z = zipfile.ZipFile(apk)
    data = z.read(dpath)
    hdr_size = 112
    string_ids_size, string_ids_off = struct.unpack_from('<II', data, 56)
    type_ids_size, type_ids_off = struct.unpack_from('<II', data, 64)
    _, proto_off = struct.unpack_from('<I', data, 72)[:1], 0
    field_ids_size, field_ids_off = struct.unpack_from('<II', data, 80)
    method_ids_size, method_ids_off = struct.unpack_from('<II', data, 88)
    class_ids_size, class_defs_off = struct.unpack_from('<II', data, 96)
    def tname(ti):
        di = struct.unpack_from('<I', data, type_ids_off + ti*4)[0]
        return string_at(data, string_ids_off, di, None)
    want = sys.argv[2] if len(sys.argv) > 2 else None
    for i in range(class_ids_size):
        off = class_defs_off + i*32
        cls_idx, access, sup_idx = struct.unpack_from('<III', data, off)
        cn = tname(cls_idx)
        if want and want not in cn: continue
        sn = tname(sup_idx) if sup_idx != 0xFFFFFFFF else '<none>'
        print(f"{cn:70} -> {sn}")

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'classes.dex')
