#!/usr/bin/env python3
"""Decode the packed-switch payload in Le/b.b (microtimer) — FORGOTTEN-005 hostile case:
determine first_key and per-key targets. Law: targets are relative to the *switch opcode* pc.
"""
import struct, zipfile, sys

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

str_off, s_sz = u4(0x3C), u4(0x38)
type_off = u4(0x44); proto_off = u4(0x4C)
f_off = u4(0x54); m_off, m_sz = u4(0x5C), u4(0x58)
c_off, c_sz = u4(0x64), u4(0x60)

def get_str(i):
    off = u4(str_off + 4 * i)
    r, p = uleb(off)
    return d[p:p + r].split(b"\x00")[0].decode("utf-8", "replace")

def type_of(i): return get_str(u4(type_off + 4 * i))

want_cls, want_meth = "Le/b;", "b"
for i in range(c_sz):
    off = c_off + 32 * i
    tn = type_of(u4(off))
    if tn != want_cls: continue
    cdo = u4(off + 24)
    p = cdo
    sf, p = uleb(p); iff, p = uleb(p)
    dm, p = uleb(p); vm, p = uleb(p)
    for _ in range(sf + iff):
        _, p = uleb(p); _, p = uleb(p)
    found_v = False
    for lst in ("direct", "virtual"):
        midx = 0
        count = dm if lst == "direct" else vm
        for _ in range(count):
            d1, p = uleb(p); d2, p = uleb(p); d3, p = uleb(p)
            midx += d1
            if midx >= m_sz or not d3: continue
            if get_str(u4(m_off + 8 * midx + 4)) != want_meth: continue
            found_v = True
            isz = u4(d3 + 12)
            code = d3 + 16
            ncodes = isz
            hits = 0
            for cu in range(ncodes):
                w = u2(code + 2 * cu)
                if w == 0x0100:
                    hits += 1
                    psize = u2(code + 2 * cu + 2)
                    first_key = u4(code + 2 * cu + 4)
                    print(f"[{lst}] packed-switch-payload at code-unit {cu:#x}: size={psize} first_key={first_key}")
                    for k in range(psize):
                        tgt = struct.unpack_from("<i", d, code + 2 * cu + 8 + 4 * k)[0]
                        print(f"  key {first_key + k} -> abs {(4 + tgt):#06x} (rel {tgt})")
            if not hits:
                print(f"[{lst}] method {want_cls}.{want_meth} words={isz}: NO packed-switch-payload ident found")
    if not found_v:
        print(f"method {want_cls}.{want_meth} not found")
