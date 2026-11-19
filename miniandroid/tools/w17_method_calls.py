#!/usr/bin/env python3
"""W17: authoritative method call-lister — dump_method_v2's PROVEN location
logic (plain uleb diffs, field/method offsets from the DEX header, all
*.dex) + the real instruction-size table walker from w16_invoke_xref for
the invoke-* scan. Validated against the runtime's APP-INVOKE call graph.

Usage: python3 w17_method_calls.py <apk> <class-desc> <method> [max]
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
    apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
    max_m = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    shown = 0
    with zipfile.ZipFile(apk) as z:
        for dex_name in sorted(n for n in z.namelist()
                               if n.endswith('.dex')):
            data = z.read(dex_name)
            h = lambda i: struct.unpack_from('<I', data, i)[0]
            cdef_off, cdef_size = h(0x64), h(0x60)
            for ci in range(cdef_size):
                row = struct.unpack_from('<8I', data, cdef_off + 32 * ci)
                if type_desc(data, row[0]) != cls or not row[6]:
                    continue
                cdo = row[6]
                sf, o = uleb(data, cdo)
                inf, o = uleb(data, o)
                dm, o = uleb(data, o)
                vm, o = uleb(data, o)
                for _ in range(sf):
                    _, o = uleb(data, o)
                    _, o = uleb(data, o)
                for _ in range(inf):
                    _, o = uleb(data, o)
                    _, o = uleb(data, o)
                # plain method_idx diff, RESET at the virtual boundary —
                # the engine's own dex_parser.cpp semantics (line ~1254/1317)
                p = 0
                for kind, cnt in (('direct', dm), ('virtual', vm)):
                    p = 0 if kind == 'virtual' else p
                    for _ in range(cnt):
                        d, o = uleb(data, o)
                        p += d
                        acc, o = uleb(data, o)
                        co, o = uleb(data, o)
                        if co == 0:
                            continue
                        _, _, name_i = struct.unpack_from(
                            '<HHI', data, h(METHODS_OFF) + 8 * p)
                        if string_at(data, name_i) != meth:
                            continue
                        regs, ins_, outs, tries, dbg, insns = \
                            struct.unpack_from('<HHHHII', data, co)
                        print(f'=== {cls}.{meth} ({kind}, regs={regs} '
                              f'ins={ins_} insns={insns}, {dex_name})')
                        class _D:
                            pass
                        d_ = _D()
                        d_.d = data
                        for pc, m in scan_all_calls(d_, co + 16, insns):
                            rc, rm = method_ref(data, m)
                            print(f'  @{pc:4d} invoke {rc}->{rm}')
                        shown += 1
                        if shown >= max_m:
                            return
    print(f'# {cls}.{meth}: {shown} variant(s) shown')


if __name__ == '__main__':
    main()
