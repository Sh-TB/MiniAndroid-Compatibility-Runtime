#!/usr/bin/env python3
"""Dump a method's bytecode words from classes.dex (minimal DEX walker).
MASTER campaign forensics: ground-truth app semantics before any law fix."""
import struct, zipfile, sys

apk, cls_want, meth_want = sys.argv[1], sys.argv[2], sys.argv[3]
z = zipfile.ZipFile(apk)
d = z.read('classes.dex')
u4 = lambda o: struct.unpack_from('<I', d, o)[0]
u2 = lambda o: struct.unpack_from('<H', d, o)[0]
u1 = lambda o: d[o]
str_off, type_off, m_off = u4(0x3c), u4(0x44), u4(0x5c)
c_off, c_sz, t_sz, s_sz = u4(0x64), u4(0x60), u4(0x40), u4(0x38)


def uleb(p):
    r = 0; s = 0
    while True:
        b = u1(p + s); r |= (b & 0x7f) << (7 * s); s += 1
        if not (b & 0x80):
            return r, p + s


def get_str(idx):
    if idx >= s_sz:
        return '<bad_str:%d>' % idx
    off = u4(str_off + 4 * idx)
    r, p2 = uleb(off)
    if p2 + r > len(d):
        return '<bad_data>'
    return d[p2:p2 + r].split(b'\x00')[0].decode('utf-8', 'replace')


def get_type(idx):
    if idx >= t_sz:
        return '<bad_type>'
    return get_str(u4(type_off + 4 * idx))


for i in range(c_sz):
    try:
        off = c_off + 32 * i
        tn = get_type(u4(off))
        if tn != cls_want:
            continue
        cdo = u4(off + 24)
        if not cdo:
            continue
        p = cdo
        sf, p = uleb(p); iff, p = uleb(p); dm, p = uleb(p); vm, p = uleb(p)
        for _ in range(sf + iff):
            _, p = uleb(p); _, p = uleb(p)
        midx = 0
        for _ in range(dm + vm):
            d1, p = uleb(p); d2, p = uleb(p); d3, p = uleb(p)
            midx += d1
            if midx >= u4(0x58):
                break
            m = u4(m_off + 8 * midx)
            name = get_str(u4(m))
            if name == meth_want and d3:
                isz = u4(d3 + 12)
                insns = d[d3 + 16:d3 + 16 + isz * 2]
                words = [struct.unpack_from('<H', insns, k)[0]
                         for k in range(0, len(insns), 2)]
                print(f'{tn} {meth_want} regs={u2(d3)} ins={u2(d3+2)} words={isz}')
                print(' '.join('%04x' % w for w in words))
    except Exception as e:
        print(f'[skip class {i}: {e}]', file=sys.stderr)
