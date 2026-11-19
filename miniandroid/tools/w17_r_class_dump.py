#!/usr/bin/env python3
"""W17: dump R$* classes' static fields + their default values (from the
class_def static_values encoded_array) and optionally the <clinit> sput
count, to diagnose which R families the CONT48-F1 harvest can see.

Usage: python3 w17_r_class_dump.py <apk> [<name-filter>]
"""
import struct
import sys
import zipfile


def uleb(data, off):
    r = 0
    sh = 0
    while True:
        b = data[off]
        off += 1
        r |= (b & 0x7F) << sh
        if not (b & 0x80):
            break
        sh += 7
    return r, off


def string_at(data, str_off, idx):
    so = struct.unpack_from('<I', data, str_off + 4 * idx)[0]
    _, o = uleb(data, so)
    e = data.index(b'\x00', o)
    return data[o:e].decode('utf-8', 'replace')


# encoded_value header: (value_arg << 3) | value_type
VALUE_TYPES = {0x00: 'byte', 0x02: 'short', 0x03: 'char', 0x04: 'int',
               0x06: 'long', 0x10: 'float', 0x11: 'double',
               0x15: 'method_type', 0x16: 'method_handle',
               0x17: 'string', 0x18: 'type', 0x19: 'field',
               0x1a: 'method', 0x1b: 'enum', 0x1c: 'array',
               0x1d: 'annotation', 0x1e: 'null', 0x1f: 'boolean'}


def read_encoded_value(data, off):
    head = data[off]
    off += 1
    vtype = head & 0x1F
    varg = (head >> 5) & 0x07
    size = varg + 1
    if vtype == 0x1e:  # null
        return None, off
    if vtype == 0x1f:  # boolean — value in value_arg
        return bool(varg), off
    raw = int.from_bytes(data[off:off + size], 'little')
    off += size
    if vtype == 0x17:  # string → resolve via string_ids
        so = struct.unpack_from('<I', data, 0x3c)[0]
        return string_at(data, so, raw), off
    return raw, off


def main():
    apk = sys.argv[1]
    filt = sys.argv[2] if len(sys.argv) > 2 else 'R$'
    with zipfile.ZipFile(apk) as z:
        for dex_name in sorted(n for n in z.namelist()
                               if n.endswith('.dex')):
            data = z.read(dex_name)
            h = lambda i: struct.unpack_from('<I', data, i)[0]
            str_off = h(0x3c)
            type_off, type_size = h(0x44), h(0x40)
            cdef_off, cdef_size = h(0x64), h(0x60)
            for ci in range(cdef_size):
                row = struct.unpack_from('<8I', data, cdef_off + 32 * ci)
                # class_idx is a TYPE index → type_ids → descriptor_idx
                d_idx = struct.unpack_from('<I', data, type_off + 4 * row[0])[0]
                tdesc = string_at(data, str_off, d_idx)
                if filt not in tdesc or 'R$' not in tdesc:
                    continue
                cdo, svo = row[6], row[7]
                print(f'=== {tdesc} ({dex_name}) class_data={cdo} '
                      f'static_values={svo}')
                if not cdo:
                    continue
                sf, o = uleb(data, cdo)
                inf, o = uleb(data, o)
                dm, o = uleb(data, o)
                vm, o = uleb(data, o)
                fld_idx = 0
                fields = []
                for _ in range(sf):
                    d, o = uleb(data, o)   # field_idx_diff — PLAIN uleb
                    fld_idx += d
                    acc, o = uleb(data, o)
                    fields.append(fld_idx)
                # defaults
                defaults = {}
                if svo:
                    n, o2 = uleb(data, svo)
                    for _ in range(n):
                        v, o2 = read_encoded_value(data, o2)
                        defaults[len(defaults)] = v
                # field_ids_off = 0x52 (0x58 is method_ids!)
                fid_off = h(0x54)  # field_ids_off (0x58/0x5C = method_ids)
                for i, f in enumerate(fields):
                    _, _, name_i = struct.unpack_from(
                        '<HHI', data, fid_off + 8 * f)
                    nm = string_at(data, str_off, name_i)
                    dv = defaults.get(i, '<no-static-value>')
                    print(f'    {nm} = {dv}')


if __name__ == '__main__':
    main()
