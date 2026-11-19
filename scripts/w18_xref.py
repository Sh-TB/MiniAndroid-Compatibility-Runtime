#!/usr/bin/env python3
"""W18: find callers of a target method across the whole DEX, using the
W17-validated walker (plain uleb diffs, reset at the virtual boundary)
+ the real instruction-size table invoke scan.

Usage: python3 w18_xref.py <apk> <type-substring> <method> [max]
"""
import struct
import sys
import zipfile

sys.path.insert(0, '/home/z/my-project/scripts')
if not __import__('os').path.exists(
        '/home/z/my-project/scripts/w16_invoke_xref.py'):
    sys.path.insert(0, '/home/z/my-project/miniandroid/tools')
from w16_invoke_xref import scan_all_calls  # noqa: E402

FIELDS_OFF, METHODS_OFF, STRINGS_OFF, TYPES_OFF = 0x54, 0x5C, 0x3C, 0x44


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


def string_at(data, idx):
    str_off = struct.unpack_from('<I', data, STRINGS_OFF)[0]
    so = struct.unpack_from('<I', data, str_off + 4 * idx)[0]
    _, o = uleb(data, so)
    e = data.index(b'\x00', o)
    return data[o:e].decode('utf-8', 'replace')


def type_desc(data, type_idx):
    type_off = struct.unpack_from('<I', data, TYPES_OFF)[0]
    return string_at(data, struct.unpack_from('<I', data, type_off + 4 * type_idx)[0])


def method_ref(data, idx):
    mth_off = struct.unpack_from('<I', data, METHODS_OFF)[0]
    cls_i, _, name_i = struct.unpack_from('<HHI', data, mth_off + 8 * idx)
    return type_desc(data, cls_i), string_at(data, name_i)


def main():
    apk, want_type, want_m = sys.argv[1], sys.argv[2], sys.argv[3]
    max_hits = int(sys.argv[4]) if len(sys.argv) > 4 else 20
    hits = 0
    with zipfile.ZipFile(apk) as z:
        for dex_name in sorted(n for n in z.namelist()
                               if n.endswith('.dex')):
            data = z.read(dex_name)
            h = lambda i: struct.unpack_from('<I', data, i)[0]
            cdef_off, cdef_size = h(0x64), h(0x60)
            for ci in range(cdef_size):
                row = struct.unpack_from('<8I', data, cdef_off + 32 * ci)
                owner_cls = type_desc(data, row[0])
                if not row[6]:
                    continue
                cdo = row[6]
                sf, o = uleb(data, cdo)
                inf, o = uleb(data, o)
                dm, o = uleb(data, o)
                vm, o = uleb(data, o)
                for _ in range(sf + inf):
                    _, o = uleb(data, o)
                    _, o = uleb(data, o)
                p = 0
                for kind, cnt in (('direct', dm), ('virtual', vm)):
                    if kind == 'virtual':
                        p = 0
                    for _ in range(cnt):
                        d, o = uleb(data, o)
                        p += d
                        acc, o = uleb(data, o)
                        co, o = uleb(data, o)
                        if co == 0:
                            continue
                        _, _, name_i = struct.unpack_from(
                            '<HHI', data, h(METHODS_OFF) + 8 * p)
                        meth = string_at(data, name_i)
                        class _D:
                            pass
                        d_ = _D()
                        d_.d = data
                        try:
                            for pc, m in scan_all_calls(d_, co + 16,
                                                        struct.unpack_from(
                                                            '<H', data, co + 12)[0]):
                                rc, rm = method_ref(data, m)
                                if want_type in rc and rm == want_m:
                                    print(f'{owner_cls}.{meth} @{pc} '
                                          f'-> {rc}->{rm}')
                                    hits += 1
                                    if hits >= max_hits:
                                        return
                        except Exception:
                            pass
    print(f'# {hits} hits for {want_type}->{want_m}')


if __name__ == '__main__':
    main()
