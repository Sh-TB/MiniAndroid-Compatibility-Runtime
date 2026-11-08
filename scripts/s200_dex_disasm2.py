#!/usr/bin/env python3
"""S200 Target B — DEX method disassembler (verified parse).
Usage: s200_dex_disasm2.py <class-desc> [method-name-filter (comma, empty=all)]
Prints invoke targets and returns per instruction word scan."""
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


soff, toff = u4(0x3c), u4(0x44)
moff = u4(0x5c)
cdefs, coff = u4(0x60), u4(0x64)


def get_str(idx):
    off = u4(soff + 4 * idx)
    n, p = uleb(off)
    return DEX[p:p + n].decode('utf-8', 'replace')


def type_str(i):
    return get_str(u4(toff + 4 * i))


def mstr(i):
    o = moff + 8 * i
    return type_str(u2(o)) + '->' + get_str(u4(o + 4))


INVOKE = {0x6e: ('invoke-virtual', 3), 0x6f: ('invoke-super', 3),
          0x70: ('invoke-direct', 3), 0x71: ('invoke-static', 3),
          0x72: ('invoke-interface', 3)}
RET = {0x0e: 'return-void', 0x0f: 'return', 0x10: 'return-wide',
       0x11: 'return-object'}


def dump(desc, wanted):
    hit = False
    for i in range(cdefs):
        o = coff + 32 * i
        if type_str(u4(o)) != desc:
            continue
        hit = True
        cd = u4(o + 24)
        q = cd
        sf, q = uleb(q); icc, q = uleb(q); dmc, q = uleb(q); vmc, q = uleb(q)
        for _ in range(sf + icc):
            _, q = uleb(q); _, q = uleb(q)
        midx = 0
        for cnt, kind in ((dmc, 'direct'), (vmc, 'virtual')):
            for _ in range(cnt):
                diff, q = uleb(q); midx += diff
                acc, q = uleb(q); code, q = uleb(q)
                full = mstr(midx)
                name = full.split('->')[1]
                if wanted and name not in wanted:
                    continue
                if code == 0:
                    print(f"  {kind} {full} (no code)")
                    continue
                n = u4(code + 12)
                words = struct.unpack_from(f'<{n}H', DEX, code + 16)
                print(f"  {kind} {full} regs={u2(code)} insns={n}")
                i2 = 0
                while i2 < n:
                    op = words[i2] & 0xff
                    if op in INVOKE:
                        nm, sz = INVOKE[op]
                        print(f"    pc={i2*2:#06x} {nm} {mstr(words[i2+1])}")
                        i2 += sz
                    elif op in RET:
                        print(f"    pc={i2*2:#06x} {RET[op]}")
                        i2 += 1
                    elif op == 0x12:  # const/4
                        print(f"    pc={i2*2:#06x} const/4 v{(words[i2]>>8)&0xf}={(words[i2]>>12)&0xf}")
                        i2 += 1
                    elif op in (0x54, 0x59, 0x5a, 0x61, 0x52, 0x53):  # iget/iput family
                        print(f"    pc={i2*2:#06x} field-op op={op:#04x}")
                        i2 += 2
                    elif op == 0x8f or op in range(0x90, 0xaf):
                        i2 += 1
                    else:
                        i2 += 1
    if not hit:
        print('class not found:', desc)


desc = sys.argv[1]
wanted = set(sys.argv[2].split(',')) if len(sys.argv) > 2 and sys.argv[2] else None
dump(desc, wanted)
