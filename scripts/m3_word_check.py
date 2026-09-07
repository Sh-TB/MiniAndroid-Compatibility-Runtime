#!/usr/bin/env python3
"""Hexdump the exact code units around MainActivity.e pc=0x5c..0x71
to settle the runtime-vs-disassembler word decoding dispute.
DEX law: code units are 16-bit LITTLE-ENDIAN; 12x format = B|A|op.
"""
import struct, zipfile

APK = "/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/exp076_corpus/dubrowgn.microtimer_8.apk"
z = zipfile.ZipFile(APK)
d = z.read("classes.dex")

def u4(o): return struct.unpack_from("<I", d, o)[0]
def u2(o): return struct.unpack_from("<H", d, o)[0]
def uleb(p):
    r = s = 0
    while True:
        b = d[p]; p += 1
        r |= (b & 0x7F) << s; s += 7
        if not b & 0x80: return r, p

str_off = u4(0x3C)
type_off = u4(0x44)
m_off, m_sz = u4(0x5C), u4(0x58)
c_off, c_sz = u4(0x64), u4(0x60)

def get_str(i):
    off = u4(str_off + 4 * i)
    r, p = uleb(off)
    return d[p:p + r].split(b"\x00")[0].decode("utf-8", "replace")

def type_of(i): return get_str(u4(type_off + 4 * i))

for i in range(c_sz):
    off = c_off + 32 * i
    tn = type_of(u4(off))
    if tn != "Ldubrowgn/microtimer/MainActivity;":
        continue
    cdo = u4(off + 24)
    p = cdo
    sf, p = uleb(p); iff, p = uleb(p)
    dm, p = uleb(p); vm, p = uleb(p)
    for _ in range(sf + iff):
        _, p = uleb(p); _, p = uleb(p)
    for cnt in (dm, vm):
        midx = 0
        for _ in range(cnt):
            d1, p = uleb(p); d2, p = uleb(p); d3, p = uleb(p)
            midx += d1
            if midx >= m_sz or not d3:
                continue
            name = get_str(u4(m_off + 8 * midx + 4))
            if name != "e":
                continue
            isz = u4(d3 + 12)
            code = d3 + 16
            print(f"MainActivity.e code_off={code:#x} code_units={isz}")
            for cu in range(0x5c, 0x72):
                w = u2(code + 2 * cu)
                b0 = w & 0xFF
                print(f"  pc={cu:#06x} ({cu:3d})  bytes={d[code + 2*cu]:02x} {d[code + 2*cu + 1]:02x}  word={w:#06x}  op={b0:#04x}")
