#!/usr/bin/env python3
"""S104 FINAL: payload of MatcherMatchResult.<init>(SavedStateRegistryImpl;B) —
proven uleb walk + raw payload decode."""
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

def proto_params(proto_idx):
    po = u4(d, 0x4c) + proto_idx * 12
    pin = u4(d, po + 8)
    params = []
    if pin:
        for k in range(u4(d, pin)):
            params.append(get_type(u2(d, pin + 4 + k * 2)))
    return params

TARGET = "Lkotlin/text/MatcherMatchResult;"
for ci in range(class_defs):
    coff = class_off + ci * 32
    if get_type(u4(d, coff)) != TARGET: continue
    cdo = u4(d, coff + 24); o = cdo
    sf, o = uleb(d, o); inf, o = uleb(d, o); dm, o = uleb(d, o); vm, o = uleb(d, o)
    fidx = 0
    for _ in range(sf + inf):
        di, o = uleb(d, o); _, o = uleb(d, o); fidx += di
    midx = 0
    for _ in range(dm):
        di, o = uleb(d, o); _, o = uleb(d, o); midx += di
        name = get_str(u4(d, method_off + midx * 8 + 4))
        code_off, o = uleb(d, o)
        midx += 1
        if name != "<init>":
            continue
        ps = ", ".join(proto_params(u2(d, method_off + (midx - 1) * 8 + 2)))
        print(f"direct <init>({ps}) code_off={code_off:#x}")
        if "SavedStateRegistryImpl" not in ps:
            continue
        insns_size = u4(d, code_off + 12)
        insns_off = code_off + 16
        print(f"TARGET CTOR: insns_size={insns_size} units")
        blob = d[insns_off:insns_off + insns_size * 2]
        print("hex:", " ".join(f"{b:02x}" for b in blob))
        cu = 0
        while cu < insns_size:
            boff = cu * 2
            op = blob[boff + 1]; lo = blob[boff]
            if op == 0x00 and lo == 0x01:
                size, first_key = struct.unpack_from("<HH", blob, boff + 2)
                tg = struct.unpack_from(f"<{size}h", blob, boff + 6)
                print(f"pc={cu} packed-switch-payload size={size} first_key={first_key} targets={tg}")
                cu += 4 + size * 2
                continue
            if op == 0x00 and lo == 0x02:
                size = struct.unpack_from("<H", blob, boff + 2)[0]
                keys = struct.unpack_from(f"<{size}i", blob, boff + 4)
                tg = struct.unpack_from(f"<{size}i", blob, boff + 4 + size * 4)
                print(f"pc={cu} sparse-switch-payload keys={keys} targets={tg}")
                cu += 2 + size * 4
                continue
            if op == 0x00 and lo == 0x03:
                ew = u2(blob, boff + 2); sz = u4(blob, boff + 4)
                print(f"pc={cu} fill-array-data-payload ew={ew} sz={sz}")
                cu += 4 + (sz * ew + 1) // 2
                continue
            if op == 0x2b:
                t = struct.unpack_from("<i", blob, boff + 2)[0]
                print(f"pc={cu} packed-switch -> payload@pc={cu + t}")
            if op == 0x2c:
                t = struct.unpack_from("<i", blob, boff + 2)[0]
                print(f"pc={cu} sparse-switch -> payload@pc={cu + t}")
            cu += 1
