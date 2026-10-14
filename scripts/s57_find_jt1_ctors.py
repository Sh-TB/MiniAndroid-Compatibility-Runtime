#!/usr/bin/env python3
"""s57_find_jt1_ctors.py — scan dooz dex for new-instance 0x22 / invoke of Ljt1;
and report the enclosing method (class;name). Uses cont9_dexdump.Dex parser."""
import sys, zipfile, struct
import importlib.util
spec = importlib.util.spec_from_file_location("dexdump", "/home/z/my-project/scripts/cont9_dexdump.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
TARGET = sys.argv[1] if len(sys.argv) > 1 else 'Ljt1;'

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7f) << s; s += 7
        if not x & 0x80: return r, o

z = zipfile.ZipFile(APK)
data = z.read('classes.dex')
str_size, str_off = struct.unpack_from('<II', data, 56)
type_size, type_off = struct.unpack_from('<II', data, 64)
proto_size, proto_off = struct.unpack_from('<II', data, 72)
field_size, field_off = struct.unpack_from('<II', data, 80)
meth_size, meth_off = struct.unpack_from('<II', data, 88)

def getstr(i):
    o = struct.unpack_from('<I', data, str_off + 4*i)[0]
    _, p = uleb(data, o)
    e = data.index(b'\x00', p)
    return data[p:e].decode('utf-8', 'replace')

ti = None
for i in range(type_size):
    sidx = struct.unpack_from('<I', data, type_off + 4*i)[0]
    if getstr(sidx) == TARGET:
        ti = i; break
assert ti is not None, f"{TARGET} not in type table"

# method_id table: idx -> (class_idx(u16), proto_idx(u16), name_idx(u32))
def method_ref(idx):
    class_idx, proto_idx, name_idx = struct.unpack_from('<HHI', data, meth_off + 8*idx)
    return getstr(struct.unpack_from('<I', data, type_off + 4*class_idx)[0]), getstr(name_idx)

def type_of(idx):
    sidx = struct.unpack_from('<I', data, type_off + 4*idx)[0]
    return getstr(sidx)

d = mod.Dex(data)
found = []
# iterate classes via Dex parser
for off in d.iter_class_offsets() if hasattr(d, 'iter_class_offsets') else []:
    pass

# The Dex class may not expose iteration; do it raw: class_def table at 96
class_size, class_off = struct.unpack_from('<II', data, 96)
for ci in range(class_size):
    base = class_off + 32*ci
    class_idx, access, super_idx, ifaces, src, ann, cdoff = struct.unpack_from('<IIIIIII', data, base)
    cdtype = type_of(class_idx)
    if cdoff == 0: continue
    # class_data: uleb fields
    o = cdoff
    sf, inf, dm, vm = (uleb(data, o + (0,))[0] for _ in range(0)), 0, 0, 0
    sf, o = uleb(data, o); inf, o = uleb(data, o); dm, o = uleb(data, o); vm, o = uleb(data, o)
    # skip static+instance fields (2 ulebs each)
    for _ in range(sf + inf):
        _, o = uleb(data, o); _, o = uleb(data, o)
    def skip_and_code(o, n):
        entries = []
        for _ in range(n):
            m_idx, o = uleb(data, o); acc, o = uleb(data, o); coff_, o = uleb(data, o)
            entries.append((m_idx, acc, coff_, coff_))
        return entries, o
    directs, o = skip_and_code(o, dm)
    virtuals, o = skip_and_code(o, vm)
    for m_idx, acc, csize, coff in directs + virtuals:
        if coff == 0: continue
        # code_item header: regs(u16) ins(u16) outs(u16) tries(u16) debug(u32) insns_size(u32)
        insns_size = struct.unpack_from('<I', data, coff + 12)[0]
        code = data[coff+16:coff+16+insns_size*2]
        # scan for new-instance 0x22 (format 21c: 22 AA BBBB) and const-class 0x1c
        i = 0
        while i + 4 <= len(code):
            op = code[i]
            if op == 0x22:
                ty = struct.unpack_from('<H', code, i+2)[0]
                if ty == ti:
                    try:
                        cn = method_ref(m_idx)
                    except Exception:
                        cn = ('?', '?')
                    found.append((cdtype, cn[0], cn[1], 'new-instance'))
            i += 2
for f in found[:40]:
    print(f"enclosing-class={f[0]}  ref={f[1]}->{f[2]}  op={f[3]}")
print(f"TOTAL new-instance {TARGET}: {len(found)}")
