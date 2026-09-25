#!/usr/bin/env python3
"""S104: disassemble LocalSavedStateRegistryOwnerKt.<clinit> and
SavedStateViewModelFactory_androidKt.findMatchingConstructor (next divergences)."""
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
string_off = u4(d, 0x3c); type_off = u4(d, 0x44); method_off = u4(d, 0x5c)
field_off = u4(d, 0x54)
class_off = u4(d, 0x64); class_defs = u4(d, 0x60)
def get_str(idx):
    off = u4(d, string_off + idx * 4)
    n, o = uleb(d, off); end = o
    while d[end] != 0: end += 1
    return d[o:end].decode("utf-8", errors="replace")
def get_type(i): return get_str(u4(d, type_off + i * 4))
def get_m(idx):
    cls = get_type(u2(d, method_off + idx * 8))
    nm = get_str(u4(d, method_off + idx * 8 + 4))
    return f"{cls}->{nm}"

WANT = {
    "Landroidx/savedstate/compose/LocalSavedStateRegistryOwnerKt;": ("<clinit>", 60),
    "Landroidx/lifecycle/SavedStateViewModelFactory_androidKt;": ("findMatchingConstructor", 30),
}
for ci in range(class_defs):
    coff = class_off + ci * 32
    cn = get_type(u4(d, coff))
    if cn not in WANT: continue
    want_name, window = WANT[cn]
    cdo = u4(d, coff + 24); o = cdo
    sf, o = uleb(d, o); inf, o = uleb(d, o); dm, o = uleb(d, o); vm, o = uleb(d, o)
    fidx = 0
    for _ in range(sf + inf):
        di, o = uleb(d, o); _, o = uleb(d, o); fidx += di
    for sec, cnt in (("D", dm), ("V", vm)):
        midx = 0
        for i in range(cnt):
            di, o = uleb(d, o); _, o = uleb(d, o); midx += di
            name = get_str(u4(d, method_off + midx * 8 + 4))
            co, o = uleb(d, o); midx += 1
            if name != want_name: continue
            insns_size = u4(d, co + 12)
            blob = d[co + 16: co + 16 + insns_size * 2]
            print(f"=== {cn}.{name} insns={insns_size} ===")
            # crude per-unit walk: print unit index + word for invoke/iput window
            cu = 0
            while cu < insns_size:
                w = u2(blob, cu * 2)
                op = blob[cu * 2]
                line = f"u{cu:3d} w={w:#06x} op={op:#04x}"
                if op == 0x1a:  # const-string
                    si = u2(blob, cu*2+2)
                    line += f" const-string @{si} {get_str(si)[:40]!r}"
                elif op in (0x70, 0x71, 0x6e, 0x6f, 0x72):
                    mi = u2(blob, cu*2+2)
                    line += f" invoke {get_m(mi)}"
                elif op in (0x54, 0x5b, 0x52, 0x59):
                    fi = u2(blob, cu*2+2)
                    cls = get_type(u2(d, field_off+fi*8)); nm = get_str(u4(d, field_off+fi*8+4))
                    line += f" field {cls}.{nm}"
                print(line)
                cu += 1
