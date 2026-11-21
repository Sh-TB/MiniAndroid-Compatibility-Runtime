#!/usr/bin/env python3
"""List declared methods of one class in a dex (minimal parser)."""
import struct, sys, zipfile

def uleb(buf, off):
    r = 0; s = 0
    while True:
        b = buf[off]; off += 1
        r |= (b & 0x7f) << s
        if b < 0x80: return r, off
        s += 7

def main(apk, want):
    z = zipfile.ZipFile(apk)
    d = z.read('classes.dex')
    # header
    string_ids_size, = struct.unpack_from('<I', d, 0x38)
    string_ids_off, = struct.unpack_from('<I', d, 0x3c)
    type_ids_size, = struct.unpack_from('<I', d, 0x40)
    type_ids_off, = struct.unpack_from('<I', d, 0x44)
    method_ids_size, = struct.unpack_from('<I', d, 0x58)
    method_ids_off, = struct.unpack_from('<I', d, 0x5c)
    class_defs_size, = struct.unpack_from('<I', d, 0x60)
    class_defs_off, = struct.unpack_from('<I', d, 0x64)

    def get_str(idx):
        off, = struct.unpack_from('<I', d, string_ids_off + idx * 4)
        n, off = uleb(d, off)
        return d[off:off + n].decode('utf-8', 'replace')

    def get_type(idx):
        si, = struct.unpack_from('<I', d, type_ids_off + idx * 4)
        return get_str(si)

    def get_method(idx):
        p = method_ids_off + idx * 12  # shorty u16 + return u16 + params u32 + name u32
        name_idx, = struct.unpack_from('<I', d, p + 8)
        return get_type(struct.unpack_from('<H', d, p + 2)[0]), get_str(name_idx)

    target = 'L' + want.replace('.', '/') + ';'
    for i in range(class_defs_size):
        p = class_defs_off + i * 32
        cls_idx, = struct.unpack_from('<I', d, p)
        if get_type(cls_idx) != target:
            continue
        cls_data_off, = struct.unpack_from('<I', d, p + 24)
        off = cls_data_off
        static_f, off = uleb(d, off)
        inst_f, off = uleb(d, off)
        direct_m, off = uleb(d, off)
        virt_m, off = uleb(d, off)
        print(f'class {target}: direct={direct_m} virtual={virt_m}')
        # skip static + instance field entries (ULEB pairs)
        for _ in range(static_f + inst_f):
            _, off = uleb(d, off)
            _, off = uleb(d, off)
        idx = 0
        for section, count in (('direct', direct_m), ('virtual', virt_m)):
            print(f'  {section} methods:')
            for k in range(count):
                diff, off = uleb(d, off)
                idx += diff
                _, off = uleb(d, off)
                _, off = uleb(d, off)
                mt, mn = get_method(idx)
                print(f'    {mn} [{mt}]')
        return
    print(f'{target} NOT FOUND')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
