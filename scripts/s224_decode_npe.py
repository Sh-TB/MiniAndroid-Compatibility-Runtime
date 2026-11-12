#!/usr/bin/env python3
"""S224: decode the UP-window NPE storm — Lc41;.getValue pc=8 reading Lmo1;.c on null.
Dump Lc41, Lmo1 fields/methods, and the callers (Lto1;.d pc=268, Lyc0;.w, Ly9;.i)."""
import struct, zipfile, sys

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
z = zipfile.ZipFile(APK)
dexes = [n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]
print("dex files:", dexes)

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

def load(dex):
    str_size, str_off = struct.unpack_from("<2I", dex, 0x38)
    type_size, type_off = struct.unpack_from("<2I", dex, 0x40)
    proto_size, proto_off = struct.unpack_from("<2I", dex, 0x48)
    f_size, f_off = struct.unpack_from("<2I", dex, 0x50)
    m_size, m_off = struct.unpack_from("<2I", dex, 0x58)
    c_size, c_off = struct.unpack_from("<2I", dex, 0x60)
    str_off_arr = struct.unpack_from(f"<{str_size}I", dex, str_off)
    def str_at(si):
        if si >= str_size: return f"str@{si}??"
        off = str_off_arr[si]
        n, o = uleb(dex, off)
        raw = dex[o:o+n]
        # MUTF-8 rough decode
        try: return raw.decode('utf-8', 'replace')
        except Exception: return repr(raw)
    type_at = lambda ti: str_at(struct.unpack_from('<I', dex, type_off + ti*4)[0]) if ti < type_size else f"type@{ti}??"
    # field ids: (class_idx u16, type_idx u16, name_idx u32)
    def field_at(fi):
        if fi >= f_size: return f"field@{fi}??"
        ci, ti, ni = struct.unpack_from('<HHI', dex, f_off + fi*8)
        return f"{type_at(ci)}.{str_at(ni)}:{type_at(ti)}"
    # method ids: (class_idx u16, proto_idx u16, name_idx u32)
    def method_at(mi):
        if mi >= m_size: return f"method@{mi}??"
        ci, pi, ni = struct.unpack_from('<HHI', dex, m_off + m_off*0 + mi*8)
        return f"{type_at(ci)}.{str_at(ni)}"
    return dict(str_at=str_at, type_at=type_at, field_at=field_at, method_at=method_at,
                c_size=c_size, c_off=c_off, dex=dex, f_size=f_size, f_off=f_off)

def class_data(cx, name):
    D = cx['dex']
    for ci in range(cx['c_size']):
        coff = struct.unpack_from('<I', cx['c_off'] + ci*0 if False else D, 0) # placeholder
    return None

def find_class(cx, target):
    D = cx['dex']
    c_size, c_off = cx['c_size'], cx['c_off']
    for ci in range(c_size):
        base = c_off + ci * 32
        class_idx, access, superclass, interfaces_off, source, ann, cd_off, sv = struct.unpack_from('<8I', D, base)
        if cx['type_at'](class_idx) == target:
            return dict(idx=ci, access=access, superclass=superclass,
                        interfaces_off=interfaces_off, cd_off=cd_off, static_v=sv)
    return None

def parse_class_data(cx, cd_off, static_fields_off):
    D = cx['dex']
    o = cd_off
    sf, inf, dm, vm = [], [], [], []
    def n():
        nonlocal o
        v, o2 = uleb(D, o); o = o2; return v
    # delta-encoded index streams — accumulate!
    fidx = 0
    nsf = n()
    for _ in range(nsf):
        fd, o2 = uleb(D, o); o = o2; fidx += fd
        acc, o2 = uleb(D, o); o = o2
        sf.append(cx['field_at'](fidx) + f" acc=0x{acc:x}")
    nif = n()
    for _ in range(nif):
        fd, o2 = uleb(D, o); o = o2; fidx += fd
        acc, o2 = uleb(D, o); o = o2
        inf.append(cx['field_at'](fidx) + f" acc=0x{acc:x}")
    midx = 0
    ndm = n()
    for _ in range(ndm):
        md, o2 = uleb(D, o); o = o2; midx += md
        acc, o2 = uleb(D, o); o = o2
        co, o2 = uleb(D, o); o = o2
        dm.append((midx, acc, co))
    nvm = n()
    for _ in range(nvm):
        md, o2 = uleb(D, o); o = o2; midx += md
        acc, o2 = uleb(D, o); o = o2
        co, o2 = uleb(D, o); o = o2
        vm.append((midx, acc, co))
    return sf, inf, dm, vm, o

for target in ('Lc41;', 'Lmo1;', 'Lto1;'):
    found = False
    for dn in dexes:
        dex = z.read(dn)
        cx = load(dex)
        cls = find_class(cx, target)
        if cls:
            found = True
            print(f"=== {target} in {dn} superclass={cx['type_at'](cls['superclass'])}")
            sf, inf, dm, vm, _ = parse_class_data(cx, cls['cd_off'], 0)
            print("  static fields:", sf[:10])
            print("  instance fields:", inf[:14])
            names = [cx['method_at'](mi) for mi, acc, co in dm + vm]
            print("  methods:", names[:24])
            # keep the code offsets for the method of interest
            for mi, acc, co in dm + vm:
                mn = cx['method_at'](mi)
                print(f"    code_off=0x{co:x} {mn}")
    if not found:
        print(f"=== {target}: NOT FOUND in any dex")
