#!/usr/bin/env python3
"""Dump try/handler tables of a method from a DEX (ground truth parser)."""
import zipfile, struct, sys

APK = sys.argv[1]
CLS = sys.argv[2]
METH = sys.argv[3]

z = zipfile.ZipFile(APK)
d = z.read("classes.dex")


def u4(o):
    return struct.unpack_from("<I", d, o)[0]


def u2(o):
    return struct.unpack_from("<H", d, o)[0]


str_off = u4(0x3C); type_off = u4(0x44); m_off = u4(0x5C)
c_off = u4(0x64); c_sz = u4(0x60)


def get_str(idx):
    o = u4(str_off + 4 * idx)
    r = o; val = 0; shift = 0
    while True:
        b = d[r]; r += 1
        val |= (b & 0x7f) << shift; shift += 7
        if not (b & 0x80):
            break
    return d[r:r + val].decode("utf-8", "replace")


def get_type(idx):
    return get_str(u4(type_off + 4 * idx))


def uleb(off):
    r = off; val = 0; shift = 0
    while True:
        b = d[r]; r += 1
        val |= (b & 0x7f) << shift; shift += 7
        if not (b & 0x80):
            break
    return val, r


def sleb(off):
    r = off; val = 0; shift = 0
    while True:
        b = d[r]; r += 1
        val |= (b & 0x7f) << shift; shift += 7
        if not (b & 0x80):
            break
    if b & 0x40 and shift < 64:
        val -= (1 << shift)
    return val, r


cls_data = None
for ci in range(c_sz):
    off = c_off + 32 * ci
    if get_type(u4(off)) == CLS:
        cls_data = u4(off + 24)
        break
assert cls_data is not None, CLS

sf, p = uleb(cls_data); ff, p = uleb(p); dm, p = uleb(p); vm, p = uleb(p)
for _ in range(sf):
    _, p = uleb(p); _, p = uleb(p)
for _ in range(ff):
    _, p = uleb(p); _, p = uleb(p)
for group, cnt in (("direct", dm), ("virtual", vm)):
    midx = 0
    for _ in range(cnt):
        diff, p = uleb(p); acc, p = uleb(p); code_off, p = uleb(p)
        midx += diff
        m = m_off + 8 * midx
        name = get_str(u4(m + 4))
        if name != METH:
            continue
        regs = u2(code_off); tries = u2(code_off + 6); insns = u4(code_off + 12)
        print(f"onCreate code_off={code_off:#x} regs={regs} tries={tries} insns={insns}")
        insns_end = code_off + 16 + insns * 2
        pad = 2 if insns % 2 == 1 else 0
        to = insns_end + pad
        items = []
        for i in range(tries):
            o = to + 8 * i
            s = u2(o); c = u2(o + 2); h = u2(o + 4)
            items.append((s, s + c, h))
            print(f"try[{i}]: [{s:#x},{s + c:#x}) handler_off={h:#x}")
        hl = to + 8 * tries
        list_size, hp = uleb(hl)
        print(f"handler list size={list_size}")
        for i in range(list_size):
            sz, hp2 = sleb(hp)
            has_all = sz <= 0
            n = abs(sz)
            entries = []
            for j in range(n):
                t, hp2 = uleb(hp2)
                addr, hp2 = uleb(hp2)
                entries.append((t, hex(addr)))
            if has_all:
                addr, hp2 = uleb(hp2)
                print(f"handler[{i}]: typed {entries} catch-all @{addr:#x}")
            else:
                print(f"handler[{i}]: typed {entries}")
        raise SystemExit(0)
print("method not found")
