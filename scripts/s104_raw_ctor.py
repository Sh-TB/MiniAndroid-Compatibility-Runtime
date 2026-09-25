#!/usr/bin/env python3
"""S104: raw DEX parse — exact code_item for MatcherMatchResult.<init>(SavedStateRegistryImpl, B).
Ground-truth parse of packed-switch payload (ident/size/first_key/targets)."""
import struct, sys, zipfile

APK = "/home/z/my-project/run/s99/apks/com.vayunmathur.games.solitaire.apk"
TARGET = "Lkotlin/text/MatcherMatchResult;"
WANT_DESC = "(Landroidx/savedstate/internal/SavedStateRegistryImpl; B)V"

def u4(b, o): return struct.unpack_from("<I", b, o)[0]
def u2(b, o): return struct.unpack_from("<H", b, o)[0]
def u1(b, o): return b[o]
def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7f) << s; s += 7
        if not (x & 0x80): break
    return r, o
def sleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7f) << s; s += 7
        if not (x & 0x80): break
    if x & 0x40: r -= (1 << s)
    return r, o

zf = zipfile.ZipFile(APK)
for dexname in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
    d = zf.read(dexname)
    string_ids = u4(d, 0x38); string_off = u4(d, 0x3c)
    type_ids = u4(d, 0x40); type_off = u4(d, 0x44)
    proto_ids = u4(d, 0x48)
    field_ids = u4(d, 0x50); field_off = u4(d, 0x54)
    method_ids = u4(d, 0x58); method_off = u4(d, 0x5c)
    class_defs = u4(d, 0x60); class_off = u4(d, 0x64)

    def get_str(idx):
        off = u4(d, string_off + idx * 4)
        # uleb128 length then MUTF8
        n, o = uleb(d, off)
        end = o
        while d[end] != 0: end += 1
        return d[o:end].decode("utf-8", errors="replace")

    def get_type(idx):
        return get_str(u4(d, type_off + idx * 4))  # descriptor via string

    def get_field(idx):
        co = u2(d, field_off + idx * 4); t = u2(d, field_off + idx * 4 + 2); n = u4(d, field_off + idx * 4 + 4)
        return f"{get_type(t)}.{get_str(n)}"

    def get_method(idx):
        co = u2(d, method_off + idx * 4); p = u2(d, method_off + idx * 4 + 2); n = u4(d, method_off + idx * 4 + 4)
        return f"{get_type(co)}->{get_str(n)}"

    for ci in range(class_defs):
        coff = class_off + ci * 32
        cls_idx = u4(d, coff)
        if get_type(cls_idx) != TARGET: continue
        class_data_off = u4(d, coff + 24)
        if class_data_off == 0: continue
        o = class_data_off
        o = class_data_off
        sf, o = uleb(d, o); inf, o = uleb(d, o)
        dm, o = uleb(d, o); vm, o = uleb(d, o)
        fidx = 0
        for _ in range(sf): _, o = uleb(d, o); _, o = uleb(d, o); fidx += 1
        for _ in range(inf): _, o = uleb(d, o); _, o = uleb(d, o); fidx += 1
        def scan_methods(cnt, o):
            midx = 0
            for _ in range(cnt):
                di, o = uleb(d, o); acc, o = uleb(d, o); midx += di
                name = get_str(u4(d, method_off + midx * 4 + 4))
                proto_idx = u2(d, method_off + midx * 4 + 2)
                code_off, o = uleb(d, o)
                yield name, proto_idx, code_off
                midx += 1
            return o
        # need proto shorty/return/params — parse proto_ids
        def proto_str(pi):
            po = proto_ids + pi * 12
            rti = u4(d, po + 4); pin = u4(d, po + 8)
            params = []
            if pin:
                sz = u4(d, pin)
                for k in range(sz):
                    params.append(get_type(u2(d, pin + 4 + k * 2)))
            return f"({', '.join(params)}) -> {get_type(rti)}"
        for name, pi, code_off in list(scan_methods(dm, o)):
            if name == "<init>":
                ps = proto_str(pi)
                if "SavedStateRegistryImpl" in ps:
                    print(f"=== {TARGET}.<init> {ps} code_off={code_off:#x} dex={dexname} ===")
                    insns_size = u4(d, code_off + 12)
                    insns_off = code_off + 16
                    print(f"insns_size={insns_size} (code units)")
                    blob = d[insns_off:insns_off + insns_size * 2]
                    # walk instructions at code-unit granularity
                    cu = 0
                    while cu < insns_size:
                        boff = cu * 2
                        op = blob[boff + 1]
                        if op == 0x00 and blob[boff] == 0x01:  # packed-switch-payload ident 0x0100
                            size, first_key = struct.unpack_from("<HH", blob, boff + 2)
                            tg = struct.unpack_from(f"<{size}h", blob, boff + 6)
                            print(f"  pc={cu} packed-switch-payload size={size} first_key={first_key} targets={tg}")
                            cu += 4 + size * 2
                            continue
                        if op == 0x00 and blob[boff] == 0x02:  # sparse-switch-payload
                            size = struct.unpack_from("<H", blob, boff + 2)[0]
                            print(f"  pc={cu} sparse-switch-payload size={size}")
                            cu += 2 + size * 4
                            continue
                        if op == 0x00 and blob[boff] == 0x03:  # fill-array-data-payload
                            ew = u2(blob, boff + 2); sz = u4(blob, boff + 4)
                            print(f"  pc={cu} fill-array-data-payload elem_width={ew} size={sz}")
                            cu += 4 + (sz * ew + 1) // 2
                            continue
                        if op == 0x2b:  # packed-switch 31t
                            target = struct.unpack_from("<i", blob, boff + 2)[0]
                            print(f"  pc={cu} packed-switch v{blob[boff]} -> payload@pc={cu + target}")
                        cu += 1
