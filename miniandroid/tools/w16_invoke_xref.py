#!/usr/bin/env python3
"""W16: cross-reference scan — find all invoke-* call sites of a given
(class, method) pair inside an APK's classes.dex. Proper DEX parsing:
string_ids/type_ids/proto_ids/method_ids → class_defs → class_data →
code_items; decode invoke opcodes (35c: AA|op BBBB meth@BBBB, 3rc: 3rc
BBBB meth@BBBB) and report (caller_class, caller_method, pc).

Usage: python3 w16_invoke_xref.py <apk> <class-descriptor> <method-name>
Example:
  python3 scripts/w16_invoke_xref.py upload/handoff_apks/name.livitski.games.puzzle.android_2.apk 'Lname/livitski/games/puzzle/android/model/Game;' loadImage
"""
import struct
import sys
import zipfile


def uleb(data, off):
    result = 0
    shift = 0
    while True:
        b = data[off]
        off += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, off
        shift += 7


class Dex:
    def __init__(self, data):
        self.d = data
        h = lambda i: struct.unpack_from('<I', data, i)[0]
        self.string_ids_size, self.string_ids_off = h(0x38), h(0x3C)
        self.type_ids_size, self.type_ids_off = h(0x40), h(0x44)
        self.method_ids_size, self.method_ids_off = h(0x58), h(0x5C)
        self.class_defs_size, self.class_defs_off = h(0x60), h(0x64)

    def string(self, idx):
        off = struct.unpack_from('<I', self.d, self.string_ids_off + 4 * idx)[0]
        n, off = uleb(self.d, off)
        end = self.d.index(b'\x00', off)
        return self.d[off:end].decode('utf-8', 'replace')

    def type_desc(self, idx):
        sidx = struct.unpack_from('<I', self.d, self.type_ids_off + 4 * idx)[0]
        return self.string(sidx)

    def method_ref(self, idx):
        class_idx, proto_idx, name_idx = struct.unpack_from(
            '<HHI', self.d, self.method_ids_off + 8 * idx)
        return self.type_desc(class_idx), self.string(name_idx)

    def classes(self):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + 32 * i
            class_idx, access, super_idx, iface_off, source_idx, anno_off, \
                cd_off, static_vals = struct.unpack_from(
                    '<IIIIIIII', self.d, off)
            yield self.type_desc(class_idx), cd_off

    def class_methods(self, cd_off):
        if cd_off == 0:
            return
        off = cd_off
        sf, off = uleb(self.d, off)
        inf, off = uleb(self.d, off)
        dm, off = uleb(self.d, off)
        vm, off = uleb(self.d, off)
        for _ in range(sf):
            _, off = uleb(self.d, off)
            _, off = uleb(self.d, off)
        for _ in range(inf):
            _, off = uleb(self.d, off)
            _, off = uleb(self.d, off)
        for kind, count in (('direct', dm), ('virtual', vm)):
            midx = 0
            for _ in range(count):
                d, off = uleb(self.d, off)
                midx += d >> 1
                access, off = uleb(self.d, off)
                code_off, off = uleb(self.d, off)
                if code_off == 0:
                    yield kind, self.method_ref(midx), 0, 0
                    continue
                regs, ins, outs, tries, dbg_off, insns_size = \
                    struct.unpack_from('<HHHHII', self.d, code_off)
                yield kind, self.method_ref(midx), code_off + 16, insns_size
                # advance the ULEB stream past this entry only (the header
                # was read at the ABSOLUTE code_off, not at `off`)
                # next entry continues at `off` — nothing else to skip here.


def uleb_bytes(v):
    out = b''
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            out += bytes([b | 0x80])
        else:
            out += bytes([b])
            return out


# DEX instruction size table (code units per opcode) — per the AOSP
# dalvik-bytecode format table. Default 1 unit; 2-unit and 3-unit formats
# enumerated explicitly; payload pseudo-structures (0x0100/0x0200/0x0300
# high-byte ids under nop) handled in the walker.
_SIZES = [1] * 0x100
# 2-unit formats: 11x(most 0x0A-0x11 are 1), 21x, 21s, 21c, 21h, 21t,
# 22x, 22b, 22s, 22c, 22t, 23x, 20bc, 30x
_TWO = (
    [0x13, 0x15, 0x16, 0x19]              # const/16, const/high16, const-wide/16/32, const-wide/high16
    + [0x1A, 0x1C]                        # const-string, const-class
    + list(range(0x1D, 0x23))             # monitor/idx-family + iget/iput? no — 1D-22: check-enter, wide moves
    + [0x23, 0x24]                        # new-array, filled-new-array? 24=35c is 3 — fixed below
    + [0x27]                              # throw
    + [0x28]                              # goto/16? 28=goto (1) — fixed below
    + [0x29]                              # goto/16
    + [0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B,
       0x3C, 0x3D]                        # if-test family (22t)
    + [0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D,
       0x4E, 0x4F, 0x50, 0x51]            # aget/aput family (23x)
    + list(range(0x52, 0x5D))             # iget/iput family (22c)
    + [0x5F, 0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68,
       0x69, 0x6A, 0x6B, 0x6C]            # sget/sput family (21c)
    + list(range(0x6E, 0x73))             # invoke-kind (35c) — fixed to 3 below
    + list(range(0x74, 0x79))             # invoke-kind/range (3rc) — fixed to 3 below
    + list(range(0x7B, 0x90))             # unop/binop 1-reg/2-reg (12x)
    + list(range(0x90, 0xB0))             # binop 23x
    + list(range(0xB0, 0xD0))             # binop 2addr (12x)
    + list(range(0xD0, 0xE3))             # binop/lit16 (22s), binop/lit8 (22b)
)
for _op in _TWO:
    _SIZES[_op] = 2
for _op in [0x14, 0x15, 0x16, 0x17, 0x18]:
    _SIZES[_op] = 3                       # const (31i), const-wide (51l family)
for _op in [0x1B]:
    _SIZES[_op] = 3                       # const-string/jumbo (31c)
for _op in [0x25, 0x26]:
    _SIZES[_op] = 3                       # filled-new-array (35c)/(3rc)
for _op in list(range(0x6E, 0x73)):
    _SIZES[_op] = 3                       # invoke-kind (35c)
for _op in list(range(0x74, 0x79)):
    _SIZES[_op] = 3                       # invoke-kind/range (3rc)
for _op in [0x2A, 0x2B, 0x2C]:
    _SIZES[_op] = 3                       # goto/32, packed/sparse-switch (31t)
_SIZES[0x28] = 1                          # goto 10t
_SIZES[0x24] = 3                          # filled-new-array 35c


def insns_size_units(d, off, end):
    return 0


def scan_calls(dex, code_off, insns_size, target_idx):
    """Decode the insns stream with the real size table; report invoke hits."""
    hits = []
    off = code_off
    end = code_off + insns_size * 2
    while off + 1 < end:
        w = struct.unpack_from('<H', dex.d, off)[0]
        op = w & 0xFF
        if op == 0x00:
            # nop or payload: 0100=pad-nop(1u); sparse-switch payload 0x0100?
            # payload ids are the HIGH byte of the unit: 0x0100 (sparse), 0x0200
            # (packed), 0x0300 (fill-array data)
            high = w >> 8
            if high == 0x01:  # sparse-switch payload
                ident, size = struct.unpack_from('<HH', dex.d, off)
                total = 4 + size * 4 + size * 2
                off += (total + 1) & ~1
                continue
            if high == 0x02:  # packed-switch payload
                ident, size = struct.unpack_from('<HH', dex.d, off)
                total = 4 + size * 4 + size * 4
                off += (total + 1) & ~1
                continue
            if high == 0x03:  # fill-array-data payload
                ident, ew, size = struct.unpack_from('<HHI', dex.d, off)
                total = 8 + size * ew
                off += (total + 1) & ~1
                continue
            off += 2
            continue
        if (0x6E <= op <= 0x72) or (0x74 <= op <= 0x78):
            m = struct.unpack_from('<H', dex.d, off + 2)[0]
            if m == target_idx:
                hits.append(off)
        off += _SIZES[op] * 2
    return hits


def main():
    apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
    dump_targets = len(sys.argv) > 4 and sys.argv[4] == '--dump-calls'
    with zipfile.ZipFile(apk) as z:
        dexes = [(n, z.read(n)) for n in sorted(
            n for n in z.namelist() if n.endswith('.dex'))]
    for dex_name, data in dexes:
        try:
            dex = Dex(data)
        except Exception as e:
            print(f'# {dex_name}: parse failed {e}')
            continue
        if run(dex, dex_name, cls, meth, dump_targets):
            return
    print('# not found in any dex')


def run(dex, dex_name, cls, meth, dump_targets):
    data = dex.d
    if dump_targets:
        # list every invoke target inside cls.meth
        for cdesc, cd_off in dex.classes():
            if cdesc != cls or not cd_off:
                continue
            for kind, ref, code_off, insns in dex.class_methods(cd_off):
                if ref and ref[1] == meth:
                    print(f'=== {cls}->{meth} ({kind}, {dex_name}) insns={insns}')
                    for h, m in scan_all_calls(dex, code_off, insns):
                        rc, rm = dex.method_ref(m)
                        print(f'  @{h} invoke {rc}->{rm}')
                    return True
        return False
    # find target method index
    target = None
    for i in range(dex.method_ids_size):
        c, m = dex.method_ref(i)
        if c == cls and m == meth:
            target = i
            break
    if target is None:
        return False
    print(f'target: {dex_name} method@{target} {cls}->{meth}')
    for cdesc, cd_off in dex.classes():
        if not cd_off:
            continue
        for kind, ref, code_off, insns in dex.class_methods(cd_off):
            if ref is None:
                continue
            rcls, rname = ref
            for h in scan_calls(dex, code_off, insns, target):
                print(f'  CALLER {cdesc}->{rname} ({kind}) pc_code_off={h}')


def scan_all_calls(dex, code_off, insns_size):
    """Every invoke-* (pc, method_idx) in the insns stream."""
    out = []
    off = code_off
    end = code_off + insns_size * 2
    while off + 1 < end:
        w = struct.unpack_from('<H', dex.d, off)[0]
        op = w & 0xFF
        if op == 0x00:
            high = w >> 8
            if high == 0x01:
                _, size = struct.unpack_from('<HH', dex.d, off)
                off += (4 + size * 4 + size * 2 + 1) & ~1
                continue
            if high == 0x02:
                _, size = struct.unpack_from('<HH', dex.d, off)
                off += (4 + size * 4 + size * 4 + 1) & ~1
                continue
            if high == 0x03:
                _, ew, size = struct.unpack_from('<HHI', dex.d, off)
                off += (8 + size * ew + 1) & ~1
                continue
            off += 2
            continue
        if (0x6E <= op <= 0x72) or (0x74 <= op <= 0x78):
            m = struct.unpack_from('<H', dex.d, off + 2)[0]
            out.append((off, m))
        off += _SIZES[op] * 2
    return out


if __name__ == '__main__':
    main()
