#!/usr/bin/env python3
"""S104: decode field indices in ComponentActivity.<init> around pc=430-460 and
MatcherMatchResult ctor iput fields via field_ids."""
import struct, zipfile

zf = zipfile.ZipFile("run/s99/apks/com.vayunmathur.games.solitaire.apk")
d = zf.read("classes.dex")
def u4(b, o): return struct.unpack_from("<I", b, o)[0]
def u2(b, o): return struct.unpack_from("<H", b, o)[0]
def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7f) << s; s += 7
        if not (x & 0x80): break
    return r, o

string_off = u4(d, 0x3c); type_off = u4(d, 0x44)
field_off = u4(d, 0x54); method_off = u4(d, 0x5c)
class_off = u4(d, 0x64); class_defs = u4(d, 0x60)

def get_str(idx):
    off = u4(d, string_off + idx * 4)
    n, o = uleb(d, off); end = o
    while d[end] != 0: end += 1
    return d[o:end].decode("utf-8", errors="replace")
def get_type(i): return get_str(u4(d, type_off + i * 4))
def get_field(idx):
    cls = get_type(u2(d, field_off + idx * 8))
    typ = get_type(u2(d, field_off + idx * 8 + 2))
    nm = get_str(u4(d, field_off + idx * 8 + 4))
    return f"{cls}.{nm}:{typ}"

# scan ComponentActivity.<init> insns for iget-object/iput-object field refs
TARGET = "Landroidx/activity/ComponentActivity;"
for ci in range(class_defs):
    coff = class_off + ci * 32
    if get_type(u4(d, coff)) != TARGET: continue
    cdo = u4(d, coff + 24); o = cdo
    sf, o = uleb(d, o); inf, o = uleb(d, o); dm, o = uleb(d, o); vm, o = uleb(d, o)
    fidx = 0
    for _ in range(sf + inf):
        di, o = uleb(d, o); _, o = uleb(d, o); fidx += di
    midx = 0
    for sec, cnt in (("D", dm), ("V", vm)):
        midx = 0
        for i in range(cnt):
            di, o = uleb(d, o); _, o = uleb(d, o); midx += di
            name = get_str(u4(d, method_off + midx * 8 + 4))
            co, o = uleb(d, o); midx += 1
            if name != "<init>": continue
            insns_size = u4(d, co + 12)
            blob = d[co + 16: co + 16 + insns_size * 2]
            cu = 0
            while cu < insns_size:
                boff = cu * 2
                op = blob[boff]
                # 22c field ops: iget-object 0x54, iget 0x52, iput-object 0x5b, iput 0x59
                if op in (0x52, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f, 0x60, 0x61, 0x62):
                    fidx2 = struct.unpack_from("<H", blob, boff + 2)[0]
                    if 440 <= cu <= 460 or (op in (0x54, 0x5b) and cu >= 400):
                        print(f"CA pc={cu} op={op:#x} field[{fidx2}] = {get_field(fidx2)}")
                cu += 1
    break

# MatcherMatchResult ctor iput field indices
print("--- MMR ctor fields ---")
TARGET2 = "Lkotlin/text/MatcherMatchResult;"
for ci in range(class_defs):
    coff = class_off + ci * 32
    if get_type(u4(d, coff)) != TARGET2: continue
    cdo = u4(d, coff + 24); o = cdo
    sf, o = uleb(d, o); inf, o = uleb(d, o); dm, o = uleb(d, o); vm, o = uleb(d, o)
    fidx = 0
    for _ in range(sf + inf):
        di, o = uleb(d, o); _, o = uleb(d, o); fidx += di
        print(f"MMR field: {get_field(fidx)}")
    midx = 0
    for sec, cnt in (("D", dm),):
        midx = 0
        for i in range(cnt):
            di, o = uleb(d, o); _, o = uleb(d, o); midx += di
            name = get_str(u4(d, method_off + midx * 8 + 4))
            co, o = uleb(d, o); midx += 1
            if name != "<init>": continue
            insns_size = u4(d, co + 12)
            blob = d[co + 16: co + 16 + insns_size * 2]
            cu = 0
            while cu < insns_size:
                boff = cu * 2
                op = blob[boff]
                if op in (0x52, 0x54, 0x59, 0x5b, 0x5d):
                    fidx2 = struct.unpack_from("<H", blob, boff + 2)[0]
                    print(f"  <init> pc={cu} op={op:#x} field[{fidx2}] = {get_field(fidx2)}")
                cu += 1
    break
