#!/usr/bin/env python3
"""cont156_loz_probe.py — where is LLoz0; instantiated in dooz v23?
Raw word-aligned pattern scan (independent of the class_data walker):
  1. find Loz0; type_idx
  2. scan for new-instance (0x22, vAA, tidx) patterns
  3. list ALL method_ids whose class == LLoz0;
  4. if still nothing: list which classes REFERENCE type Loz0; via
     check-cast (0x1f) / instance-of (0x20) / const-class (0x1c) / new-array.
"""
import zipfile, struct, sys

APK = sys.argv[1] if len(sys.argv) > 1 else 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
zf = zipfile.ZipFile(APK)
dex = zf.read('classes.dex')

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1; r |= (x & 0x7f) << s
        if not (x & 0x80): break
        s += 7
    return r, o

str_size, str_off = struct.unpack_from('<2I', dex, 0x38)
type_size, type_off = struct.unpack_from('<2I', dex, 0x40)
proto_size, proto_off = struct.unpack_from('<2I', dex, 0x44)
field_size, field_off = struct.unpack_from('<2I', dex, 0x50)
meth_size, meth_off = struct.unpack_from('<2I', dex, 0x58)
class_size, class_off = struct.unpack_from('<2I', dex, 0x60)

soa = struct.unpack_from(f'<{str_size}I', dex, str_off)
def str_at(si):
    off = soa[si]; _, o = uleb(dex, off)
    return dex[o:dex.index(b'\x00', o)].decode('utf-8', 'replace')

tds = [str_at(struct.unpack_from('<I', dex, type_off + t*4)[0]) for t in range(type_size)]
loz_tidx = tds.index('Loz0;')
print(f'Loz0; type_idx = {loz_tidx} (0x{loz_tidx:04x})')

# 2. raw new-instance scan
needle = struct.pack('<H', loz_tidx)
hits = []
for off in range(0, len(dex) - 4, 2):
    if dex[off] == 0x22 and dex[off+2:off+4] == needle:
        hits.append(off)
print(f'raw (22,_,tidx) hits: {len(hits)}')

# 3. method_ids referencing Loz0;
mids_loz = []
for i in range(meth_size):
    c, p, n = struct.unpack_from('<HHI', dex, meth_off + i*8)
    if c == loz_tidx:
        mids_loz.append((i, n))
print(f'method_ids class==LLoz0;: {len(mids_loz)}')
for i, n in mids_loz[:10]:
    print(f'  mid{i} .{n}')

# 4. fields declared in Loz0; or typed Loz0;
fids_loz = []
for i in range(field_size):
    c, t, n = struct.unpack_from('<HHI', dex, field_off + i*8)
    if c == loz_tidx or t == loz_tidx:
        fids_loz.append((i, tds[c], tds[t], n))
print(f'field_ids involving Loz0;: {len(fids_loz)}')
for i, c, t, n in fids_loz[:15]:
    print(f'  fid{i} {c}.{n} : {t}')

# 5. class_def for Loz0;
for ci in range(class_size):
    cdef = class_off + ci*32
    if struct.unpack_from('<H', dex, cdef)[0] == loz_tidx:
        acc = struct.unpack_from('<H', dex, cdef + 2)[0]
        coff = struct.unpack_from('<I', dex, cdef + 24)[0]
        print(f'class_def[{ci}] Loz0; acc=0x{acc:04x} class_data_off={coff}')
        if coff:
            o = coff
            sf, o = uleb(dex, o); ifc, o = uleb(dex, o)
            dm_s, o = uleb(dex, o); dm_i, o = uleb(dex, o)
            print(f'  static_f={sf} inst_f={ifc} direct_m={dm_s} virtual_m={dm_i}')
            prev = 0
            for _ in range(sf + ifc):
                fd, o = uleb(dex, o); acc2, o = uleb(dex, o)
                print(f'    field idx={prev+fd} acc=0x{acc2:x} name={str_at(struct.unpack_from("<HHI", dex, field_off + (prev+fd)*8)[2])}')
                prev += fd
            for kind, cnt in (('direct', dm_s), ('virtual', dm_i)):
                prev = 0
                for _ in range(cnt):
                    md, o = uleb(dex, o); acc2, o = uleb(dex, o); codeoff, o = uleb(dex, o)
                    midx = prev + md; prev = midx
                    _, _, n = struct.unpack_from('<HHI', dex, meth_off + midx*8)
                    print(f'    {kind} method mid={midx} .{n} acc=0x{acc2:x} code={codeoff}')
        break
