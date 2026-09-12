#!/usr/bin/env python3
"""Minimal AXML attribute dumper — MASTER campaign §4 forensics.
Dumps element names + attributes from compiled Android binary XML so layout
laws can be verified against APK ground truth (no source guessing)."""
import struct, sys, zipfile

RES_STRING_POOL_TYPE = 0x0001
RES_XML_START_ELEMENT = 0x0102
RES_XML_RESOURCE_MAP = 0x0180


def parse_string_pool(data, off):
    (typ, hdrsz, size, count, styleCount, flags, stringsStart,
     stylesStart) = struct.unpack_from('<HHIIIIII', data, off)
    utf8 = bool(flags & (1 << 8))
    offsets = struct.unpack_from('<%dI' % count, data, off + 28)
    strs = []
    base = off + stringsStart
    for o in offsets:
        p = base + o
        if utf8:
            u16len = data[p]
            if u16len & 0x80:
                p += 2
            else:
                p += 1
            u8len = data[p]
            if u8len & 0x80:
                u8len = ((u8len & 0x7F) << 8) | data[p + 1]
                p += 2
            else:
                p += 1
            strs.append(data[p:p + u8len].decode('utf-8', 'replace'))
        else:
            u16len = struct.unpack_from('<H', data, p)[0]
            p += 2
            if u16len & 0x8000:
                u16len = ((u16len & 0x7FFF) << 16) | struct.unpack_from('<H', data, p)[0]
                p += 2
            strs.append(data[p:p + u16len * 2].decode('utf-16-le', 'replace'))
    return strs


def dump_axml(data, label):
    pos = 8  # skip RES_XML_TYPE header
    strings = None
    print(f"===== {label} =====")
    while pos < len(data) - 8:
        typ, hdrsz, size = struct.unpack_from('<HHI', data, pos)
        if typ == RES_STRING_POOL_TYPE:
            strings = parse_string_pool(data, pos)
        elif typ == RES_XML_RESOURCE_MAP:
            pass
        elif typ == RES_XML_START_ELEMENT:
            # body from pos+16: ns(4) name(4) attrStart(2) attrSize(2)
            # numAttrs(2) idIndex(2) classIndex(2) styleIndex(2)
            ns, name, attrStart, attrSize, numAttrs = struct.unpack_from(
                '<IiHHH', data, pos + 16)
            if strings and 0 <= name < len(strings):
                print(f"<{strings[name]}>")
                for i in range(numAttrs):
                    aoff = pos + 16 + attrStart + i * attrSize
                    ans, aname = struct.unpack_from('<Ii', data, aoff)
                    atype = data[aoff + 15]
                    adata = struct.unpack_from('<I', data, aoff + 16)[0]
                    nm = strings[aname] if 0 <= aname < len(strings) else '?'
                    if atype == 0x03:  # reference
                        val = f"@ref/0x{adata:08x}"
                    elif atype == 0x02:  # attribute
                        val = f"?attr/0x{adata:08x}"
                    elif atype == 0x10:  # int
                        val = str(struct.unpack_from('<i', struct.pack('<I', adata))[0])
                    elif atype == 0x12:  # boolean
                        val = 'true' if adata else 'false'
                    elif atype == 0x04:  # float
                        val = str(struct.unpack('<f', struct.pack('<I', adata))[0])
                    elif atype == 0x05:  # dimension
                        val = f"{adata >> 8}px(u{adata & 0xff})"
                    elif atype == 0x01:  # fraction
                        val = f"{adata >> 8}%(u{adata & 0xff})"
                    else:
                        val = f"t=0x{atype:02x} d=0x{adata:08x}"
                    print(f"    {nm} = {val}")
        pos += size


if __name__ == '__main__':
    apk = sys.argv[1]
    z = zipfile.ZipFile(apk)
    for name in sys.argv[2:]:
        if name == 'ALL':
            for n in z.namelist():
                if n.endswith('.xml'):
                    dump_axml(z.read(n), n)
        else:
            dump_axml(z.read(name), name)
