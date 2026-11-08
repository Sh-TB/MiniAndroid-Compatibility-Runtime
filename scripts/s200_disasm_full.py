#!/usr/bin/env python3
"""Full-width DEX disassembler for one method (S200 Target-B).
Usage: s200_disasm_full.py <class-idx> <method-name> [direct|virtual]"""
import struct, sys
from pathlib import Path

DEX = Path('/tmp/ttt/dex/classes.dex').read_bytes()
u4 = lambda o: struct.unpack_from('<I', DEX, o)[0]
u2 = lambda o: struct.unpack_from('<H', DEX, o)[0]


def uleb(o):
    r, s = 0, 0
    while True:
        b = DEX[o]; o += 1
        r |= (b & 0x7f) << s; s += 7
        if not b & 0x80:
            return r, o


soff, toff, moff = u4(0x3c), u4(0x44), u4(0x5c)
cdefs, coff = u4(0x60), u4(0x64)


def get_str(i):
    off = u4(soff + 4 * i)
    n, p = uleb(off)
    return DEX[p:p + n].decode('utf-8', 'replace')


def type_str(i):
    return get_str(u4(toff + 4 * i))


def mstr(i):
    o = moff + 8 * i
    return type_str(u2(o)) + '->' + get_str(u4(o + 4))


def width(op):
    if op in (0x00,): return 2 if False else 1
    if op in (0x13, 0x15, 0x16, 0x19, 0x1a, 0x1c, 0x1f, 0x20, 0x22, 0x23):
        return 2
    if op in (0x14, 0x17, 0x1b, 0x24, 0x25, 0x26):
        return 3
    if op == 0x18: return 5
    if 0x28 <= op <= 0x3d: return 2   # branches
    if 0x44 <= op <= 0x6d: return 2   # aget/aput/iget/iput/sget/sput
    if 0x6e <= op <= 0x78: return 3   # invokes + ranges
    if 0x90 <= op <= 0xaf: return 2   # binop
    if 0xd0 <= op <= 0xe2: return 2   # binop/lit
    return 1


def disasm(cidx, mname, kind_filter=None):
    o = coff + 32 * cidx
    cd = u4(o + 24)
    q = cd
    sf, q = uleb(q); icc, q = uleb(q); dmc, q = uleb(q); vmc, q = uleb(q)
    for _ in range(sf + icc):
        _, q = uleb(q); _, q = uleb(q)
    for base, cnt, kind in ((0, dmc, 'direct'), (0, vmc, 'virtual')):
        midx = 0
        for _ in range(cnt):
            diff, q = uleb(q); midx += diff
            acc, q = uleb(q); code, q = uleb(q)
            nm = mstr(midx)
            if nm.split('->')[1] != mname or kind != (kind_filter or 'direct'):
                continue
            n = u4(code + 12)
            words = struct.unpack_from(f'<{n}H', DEX, code + 16)
            print(f'{kind} {nm} insns={n}')
            i = 0
            while i < n:
                w = words[i]
                op = w & 0xff
                wid = width(op)
                note = ''
                if op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
                    note = 'INVOKE ' + mstr(words[i + 1])
                elif op in (0x74, 0x75, 0x76, 0x77, 0x78):
                    note = 'INVOKE-RANGE ' + mstr(words[i + 1])
                elif op == 0x1a:
                    note = 'const-string "' + get_str(words[i + 1])[:40] + '"'
                elif op == 0x22:
                    note = 'new-instance ' + type_str(words[i + 1])
                elif op == 0x23:
                    note = 'new-array ' + type_str(words[i + 1])
                elif 0x52 <= op <= 0x5f:
                    fidx = words[i + 1]
                    fo = u4(0x54 + 4 * 0)  # field_ids_off=0x54
                    fo = u4(0x54)
                    note = ('field ' + type_str(u2(fo + 8 * fidx)) + '.' +
                            get_str(u4(fo + 8 * fidx + 4)))
                print(f'  pc={i*2:#05x} op={op:#04x} w={w:#06x} {note}')
                i += wid


cidx = int(sys.argv[1])
disasm(cidx, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'direct')
