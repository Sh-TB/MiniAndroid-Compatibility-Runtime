#!/usr/bin/env python3
"""Minimal binary AXML element/attr dumper (cont59 decode aid)."""
import zipfile, struct, sys

def parse(axml):
    o = 8  # skip file header (type, size)
    chunks = []
    while o < len(axml):
        ctype, hsz, size = struct.unpack_from('<HHI', axml, o)
        if size <= 0: break
        chunks.append((ctype, o, hsz, size))
        o += size
    return chunks

def string_pool(b, sp, hsz, cnt, sstart, flags):
    strs = []
    for i in range(cnt):
        try:
            so = sp + sstart + struct.unpack_from('<I', b, sp + hsz + 4 * i)[0]
            if flags & 0x100:
                def vlen(p):
                    c = b[p]
                    if c & 0x80: return ((c & 0x7f) << 8) | b[p + 1], p + 2
                    return c, p + 1
                _, p = vlen(so); l, p = vlen(p)
                strs.append(b[p:p + l].decode('utf-8', 'replace'))
            else:
                n = struct.unpack_from('<H', b, so)[0]
                if n & 0x8000:
                    n = ((n & 0x7fff) << 16) | struct.unpack_from('<H', b, so + 2)[0]
                    so += 4
                else:
                    so += 2
                strs.append(b[so:so + n * 2].decode('utf-16-le', 'replace'))
        except Exception:
            strs.append('<err>')
    return strs

def main(apk, resname):
    z = zipfile.ZipFile(apk)
    b = z.read(resname)
    ct, hsz, size = struct.unpack_from('<HHI', b, 8)
    cnt = struct.unpack_from('<I', b, 16)[0]
    sstart = struct.unpack_from('<I', b, 28)[0]   # pool+20 = stringsStart
    flags = struct.unpack_from('<I', b, 24)[0]    # pool+16 = flags
    strs = string_pool(b, 8, hsz, cnt, sstart, flags)
    # resource id map chunk follows string pool
    pos = 8 + size
    resid_map = []
    while pos < len(b):
        ctype2, hs2, sz2 = struct.unpack_from('<HHI', b, pos)
        if ctype2 == 0x0180:  # RES_XML_RESOURCE_MAP_TYPE
            n = (sz2 - hs2) // 4
            resid_map = [struct.unpack_from('<I', b, pos + hs2 + 4 * i)[0] for i in range(n)]
            pos += sz2
            break
        pos += sz2 if sz2 else 4
    # walk start elements
    pos = pos if resid_map else 8 + size
    depth = 0
    while pos < len(b):
        ctype3, hs3, sz3 = struct.unpack_from('<HHI', b, pos)
        if ctype3 == 0x0102:  # START_ELEMENT
            name_idx = struct.unpack_from('<I', b, pos + 20)[0]
            attr_start = struct.unpack_from('<H', b, pos + 24)[0]
            attr_size = struct.unpack_from('<H', b, pos + 26)[0]
            attr_count = struct.unpack_from('<H', b, pos + 28)[0]
            elem = strs[name_idx]
            print(f"{'  ' * depth}<{elem}>")
            for i in range(attr_count):
                ao = pos + attr_start + i * attr_size
                aname, raw_idx = struct.unpack_from('<II', b, ao + 4)
                atype = b[ao + 15]
                adata = struct.unpack_from('<I', b, ao + 16)[0]
                astr = strs[raw_idx] if raw_idx != 0xFFFFFFFF else ''
                an = strs[aname] if aname != 0xFFFFFFFF else '?'
                rid = resid_map[i] if i < len(resid_map) else 0
                print(f"{'  ' * depth}   {an} = t:0x{atype:02x} d:0x{adata:x} raw:'{astr}' resid:0x{rid:08x}")
            depth += 1
        elif ctype3 == 0x0103:
            depth -= 1
        pos += sz3 if sz3 else 4

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
