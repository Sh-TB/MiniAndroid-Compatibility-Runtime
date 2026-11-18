#!/usr/bin/env python3
"""W16 hybrid DEX method-call dumper: locates methods with the proven
dump_method_v2 location logic (all dexes, correct class_data walk) and
lists every invoke-* target resolved through method_ids, using the real
instruction-size table from w16_invoke_xref. Read-only analysis tool.

Usage: python3 w16_hybrid_dump.py <apk> <class-desc> <method> [max_methods]
Example:
  python3 w16_hybrid_dump.py upload/handoff_apks/name.livitski.games.puzzle.android_2.apk \
      'Lname/livitski/games/puzzle/android/model/Game;' '<init>' 4
"""
import struct
import sys
import zipfile

sys.path.insert(0, '/home/z/my-project/scripts')
from w16_invoke_xref import scan_all_calls  # real-size-table walker


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


def main():
    apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
    max_m = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    shown = 0
    with zipfile.ZipFile(apk) as z:
        for dex_name in sorted(n for n in z.namelist()
                               if n.endswith('.dex')):
            data = z.read(dex_name)
            h = lambda i: struct.unpack_from('<I', data, i)[0]
            str_off = h(0x3c)
            type_off, type_size = h(0x44), h(0x40)
            mth_off = h(0x5c)
            cdef_off, cdef_size = h(0x64), h(0x60)

            def string(idx):
                so = struct.unpack_from('<I', data, str_off + 4 * idx)[0]
                _, o = uleb(data, so)
                e = data.index(b'\x00', o)
                return data[o:e].decode('utf-8', 'replace')

            # class descriptor → type index
            want_t = None
            for i in range(type_size):
                if string(struct.unpack_from('<I', data, type_off + 4 * i)[0]) == cls:
                    want_t = i
                    break
            if want_t is None:
                continue
            for ci in range(cdef_size):
                row = struct.unpack_from('<8I', data, cdef_off + 32 * ci)
                if row[0] != want_t or row[6] == 0:
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
                p = 0  # method_idx diff accumulates ACROSS both lists
                # (DEX spec: each encoded_method's diff is relative to the
                # previous encoded_method, continuing through the virtual
                # list — verified against the runtime's own dispatch counts)
                for kind, cnt in (('direct', dm), ('virtual', vm)):
                    for _ in range(cnt):
                        d, o = uleb(data, o)
                        p += d >> 1
                        acc, o = uleb(data, o)
                        co, o = uleb(data, o)
                        if co == 0:
                            continue
                        _, _, name_i = struct.unpack_from(
                            '<HHI', data, mth_off + 8 * p)
                        name = string(name_i)
                        if name != meth:
                            continue
                        regs, ins, outs, tries, dbg, insns = \
                            struct.unpack_from('<HHHHII', data, co)
                        print(f'=== {cls}.{meth} ({kind}, regs={regs} '
                              f'ins={ins} insns={insns}, {dex_name}) '
                              f'code_off={co}')
                        for pc, m in scan_all_calls_from(
                                data, co + 16, insns):
                            rc, rm = resolve_method(data, mth_off, str_off, m)
                            print(f'  @{pc:4d} invoke {rc}->{rm}')
                        shown += 1
                        if shown >= max_m:
                            return
    print(f'# {cls}.{meth}: {shown} variant(s) shown')


def scan_all_calls_from(data, insns_off, insns):
    """scan_all_calls needs a Dex-like object with .d — wrap raw bytes."""
    class _D:
        pass
    d = _D()
    d.d = data
    return scan_all_calls(d, insns_off, insns)


def resolve_method(data, mth_off, str_off, idx):
    cls_i, _, name_i = struct.unpack_from('<HHI', data, mth_off + 8 * idx)

    def uleb2(off):
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

    so = struct.unpack_from('<I', data, str_off + 4 * name_i)[0]
    _, o = uleb2(so)
    e = data.index(b'\x00', o)
    name = data[o:e].decode('utf-8', 'replace')
    # class descriptor via type_ids → string
    type_off = struct.unpack_from('<I', data, 0x44)[0]
    d_idx = struct.unpack_from('<I', data, type_off + 4 * cls_i)[0]
    str2_off = struct.unpack_from('<I', data, 0x3c)[0]
    so2 = struct.unpack_from('<I', data, str2_off + 4 * d_idx)[0]
    _, o2 = uleb2(so2)
    e2 = data.index(b'\x00', o2)
    desc = data[o2:e2].decode('utf-8', 'replace')
    return desc, name


if __name__ == '__main__':
    main()
