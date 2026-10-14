#!/usr/bin/env python3
"""CONT-11: verify the Ldalvik/annotation/InnerClass; SYSTEM annotation of a
class in an APK's DEX — its accessFlags element proves what Class.getModifiers
must return for member classes (ART law). Read-only evidence tool.
Usage: cont11_innerclass_check.py <apk> <Lcls;> [more classes...]"""
import sys, zipfile, struct

def uleb(data, p):
    r = 0; sh = 0
    while True:
        b = data[p]; p += 1
        r |= (b & 0x7f) << sh
        if not (b & 0x80): break
        sh += 7
    return r, p

def read_encoded_value(data, p):
    head = data[p]; p += 1
    vtype = head & 0x1f
    varg = (head >> 5) & 0x7
    size = varg + 1
    if vtype == 0x1e:  # null
        return ('null', None), p
    if vtype == 0x1f:  # bool
        return ('bool', bool(varg)), p
    if vtype == 0x00:  # byte
        return ('byte', int.from_bytes(data[p:p+1], 'little', signed=True)), p+1
    if vtype in (0x02, 0x03, 0x04, 0x05, 0x06):  # short/char/int/long
        n = size
        val = int.from_bytes(data[p:p+n], 'little')
        if vtype == 0x02: val = val if val < (1 << (n*8-1)) else val - (1 << (n*8))
        return ('int', val), p+n
    if vtype == 0x17:  # string
        idx = int.from_bytes(data[p:p+size], 'little')
        return ('string_idx', idx), p+size
    if vtype == 0x18:  # type
        idx = int.from_bytes(data[p:p+size], 'little')
        return ('type_idx', idx), p+size
    if vtype in (0x10, 0x11):  # float/double: zero-extended to the right
        raw = data[p:p+size]
        return ('fp', raw.hex()), p+size
    if vtype == 0x1c:  # array
        sz, p = uleb(data, p)
        vals = []
        for _ in range(sz):
            v, p = read_encoded_value(data, p)
            vals.append(v)
        return ('array', vals), p
    if vtype == 0x1d:  # nested annotation
        tidx, p = uleb(data, p)
        sz, p = uleb(data, p)
        elems = []
        for _ in range(sz):
            nidx, p = uleb(data, p)
            v, p = read_encoded_value(data, p)
            elems.append((nidx, v))
        return ('annot', (tidx, elems)), p
    return ('unk_%02x' % vtype, None), p + size

def main():
    apk = sys.argv[1]
    targets = set(sys.argv[2:])
    z = zipfile.ZipFile(apk)
    for name in sorted(n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')):
        data = z.read(name)
        if data[:4] != b'dex\n': continue
        string_ids_size, string_ids_off = struct.unpack_from('<II', data, 56)
        type_ids_size, type_ids_off = struct.unpack_from('<II', data, 64)
        field_ids_size, field_ids_off = struct.unpack_from('<II', data, 80)
        cd_size, cd_off = struct.unpack_from('<II', data, 96)
        strings = []
        for i in range(string_ids_size):
            (soff,) = struct.unpack_from('<I', data, string_ids_off + i*4)
            _, p = uleb(data, soff)
            e = data.index(b'\x00', p)
            strings.append(data[p:e].decode('utf-8','replace'))
        types = []
        for i in range(type_ids_size):
            (si,) = struct.unpack_from('<I', data, type_ids_off + i*4)
            types.append(strings[si])
        for ci in range(cd_size):
            cdo = cd_off + ci * 32
            class_idx, access = struct.unpack_from('<II', data, cdo)
            ann_off = struct.unpack_from('<I', data, cdo + 20)[0]
            cdata_off = struct.unpack_from('<I', data, cdo + 24)[0]
            cls = types[class_idx]
            if targets and cls not in targets: continue
            print(f"{cls}: class_def access_flags = {access:#06x}")
            if not ann_off:
                print("   (no class annotations)"); continue
            n, p0 = struct.unpack_from('<II', data, ann_off)
            for k in range(n):
                aoff = struct.unpack_from('<I', data, p0 + k*4)[0]
                vis = data[aoff]
                tidx, p = uleb(data, aoff + 1)
                tname = types[tidx]
                sz, p = uleb(data, p)
                elems = []
                for _ in range(sz):
                    nidx, p = uleb(data, p)
                    v, p = read_encoded_value(data, p)
                    elems.append((strings[nidx], v))
                visname = {0:'BUILD',1:'RUNTIME',2:'SYSTEM'}.get(vis, str(vis))
                mark = ' <== INNERCLASS' if 'InnerClass' in tname else ''
                print(f"   annotation {tname} vis={visname}{mark}")
                for en, ev in elems:
                    val = ev[1]
                    if isinstance(val, int) and ev[0] in ('string_idx',):
                        val = strings[val]
                    print(f"      {en} = {ev[0]}:{val}")
            if targets: targets.discard(cls)
            if not targets: return

if __name__ == '__main__':
    main()
