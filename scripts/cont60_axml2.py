#!/usr/bin/env python3
"""Clean binary AXML dumper (cont60 decode aid) — correct string pool + attr layout."""
import zipfile, struct, sys

def read_string_pool(b, off):
    ctype, hsz, size = struct.unpack_from('<HHI', b, off)
    assert ctype == 0x0001, hex(ctype)
    cnt, style_cnt, flags, sstart, styles_start = struct.unpack_from('<IIIII', b, off + 8)
    utf8 = bool(flags & 0x100)
    offs = [struct.unpack_from('<I', b, off + hsz + 4 * i)[0] for i in range(cnt)]
    strs = []
    base = off + sstart
    for o in offs:
        p = base + o
        if utf8:
            u16len = b[p]; p += 1
            if u16len & 0x80: u16len = ((u16len & 0x7f) << 8) | b[p]; p += 1
            l = b[p]; p += 1
            if l & 0x80: l = ((l & 0x7f) << 8) | b[p]; p += 1
            strs.append(b[p:p + l].decode('utf-8', 'replace'))
        else:
            l = struct.unpack_from('<H', b, p)[0]; p += 2
            if l & 0x8000:
                l2 = struct.unpack_from('<H', b, p)[0]; p += 2
                l = ((l & 0x7fff) << 16) | l2
            strs.append(b[p:p + l * 2].decode('utf-16-le', 'replace'))
    return strs, hsz, size

TYPES = {0x01:'ref', 0x02:'attr', 0x03:'str', 0x04:'float', 0x05:'dim',
         0x06:'frac', 0x10:'int_dec', 0x11:'int_hex', 0x12:'bool',
         0x1c:'color1', 0x1d:'color2', 0x1e:'color3', 0x1f:'color4'}

def main(apk, resname):
    z = zipfile.ZipFile(apk)
    b = z.read(resname)
    strs, sp_hsz, sp_size = read_string_pool(b, 8)
    pos = 8 + sp_size
    resid_map = []
    while pos < len(b):
        ct, hs, sz = struct.unpack_from('<HHI', b, pos)
        if ct == 0x0180:
            n = (sz - hs) // 4
            resid_map = [struct.unpack_from('<I', b, pos + hs + 4 * i)[0] for i in range(n)]
            pos += sz
            continue
        if ct == 0x0102:  # START_ELEMENT
            name_idx = struct.unpack_from('<I', b, pos + 20)[0]
            attr_start, attr_size, attr_count = struct.unpack_from('<HHH', b, pos + 24)
            print(f"<{strs[name_idx] if name_idx < len(strs) else '?'}>")
            for i in range(attr_count):
                ao = pos + attr_start + i * attr_size
                aname = struct.unpack_from('<I', b, ao + 4)[0]
                raw_idx = struct.unpack_from('<I', b, ao + 8)[0]
                atype = b[ao + 15]
                adata = struct.unpack_from('<I', b, ao + 16)[0]
                an = strs[aname] if aname < len(strs) else f'?idx{aname}'
                astr = strs[raw_idx] if raw_idx < len(strs) else ''
                tname = TYPES.get(atype, f't{atype:02x}')
                val = f'0x{adata:08x}'
                if tname == 'int_dec': val = str(struct.unpack('<i', struct.pack('<I', adata))[0])
                elif tname == 'float': val = str(struct.unpack('<f', struct.pack('<I', adata))[0])
                elif tname in ('color1','color2','color3','color4'): val = f'#{adata:08x}'
                print(f"   {an:34s} {tname:8s} {val:14s} raw:'{astr}'")
            print()
        pos += sz if sz else 4

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
