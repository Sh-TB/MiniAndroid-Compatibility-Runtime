#!/usr/bin/env python3
"""
dump_axml_attrs.py — G31 APK evidence: dump all elements + attributes from a
binary AXML file inside an APK, using only stdlib (struct/zlib).

Binary AXML chunk format (AOSP frameworks/base/libs/androidfw/include/
androidfw/ResourceTypes.h — RES_XML_* / RES_STRING_POOL_* types):
  0x0003 RES_XML_TYPE header → string pool, resource map, then chunks:
  0x0101 start-namespace, 0x0102 start-element (Attr: ns,name,raw,
  typedvalue{size,res0,dataType,data}), 0x0103 end-element.

Usage: dump_axml_attrs.py <apk> <entry>   e.g. ... res/layout/activity_main.xml
"""
import struct
import sys
import zipfile


def read_string_pool(buf, off):
    chunk_type, header_size, chunk_size = struct.unpack_from("<HHI", buf, off)
    assert chunk_type == 0x0001, hex(chunk_type)
    string_count, style_count, flags = struct.unpack_from("<III", buf, off + 8)
    strings_start, styles_start = struct.unpack_from("<II", buf, off + 20)
    utf8 = flags & (1 << 8)
    offsets = struct.unpack_from("<%dI" % string_count, buf, off + 28)
    out = []
    for o in offsets:
        p = off + strings_start + o
        if utf8:
            # u16len, u8len, then bytes
            n = buf[p]
            if n & 0x80:
                n = ((n & 0x7F) << 8) | buf[p + 1]
                p += 2
            else:
                p += 1
            ln = buf[p]
            if ln & 0x80:
                ln = ((ln & 0x7F) << 8) | buf[p + 1]
                p += 2
            else:
                p += 1
            out.append(buf[p:p + ln].decode("utf-8", "replace"))
        else:
            (n,) = struct.unpack_from("<H", buf, p)
            if n & 0x8000:
                n2 = struct.unpack_from("<H", buf, p + 2)[0]
                n = ((n & 0x7FFF) << 16) | n2
                p += 4
            else:
                p += 2
            out.append(buf[p:p + n * 2].decode("utf-16-le", "replace"))
    return out


def dump(apk_path, entry):
    with zipfile.ZipFile(apk_path) as z:
        buf = z.read(entry)
    assert buf[0] | (buf[1] << 8) == 0x0003, "not RES_XML_TYPE"

    off = 8  # skip RES_XML_TYPE header
    strings = None
    resmap = []
    out_lines = []
    while off < len(buf):
        ctype, hsize, csize = struct.unpack_from("<HHI", buf, off)
        if ctype == 0x0001:
            strings = read_string_pool(buf, off)
        elif ctype == 0x0180:
            cnt = (csize - hsize) // 4
            resmap = struct.unpack_from("<%dI" % cnt, buf, off + hsize)
        elif ctype == 0x0102:
            # ResXMLTree_attrExt: ns(4) name(4) attributeStart(2)
            # attributeSize(2) attributeCount(2) idIndex(2) classIndex(2)
            # styleIndex(2) — attributeStart is relative to THIS struct.
            base = off + hsize
            (name,) = struct.unpack_from("<I", buf, base + 4)
            attr_start, attr_size, attr_count = struct.unpack_from("<HHH", buf, base + 8)
            if strings:
                el = strings[name] if name < len(strings) else "?%d" % name
                out_lines.append("ELEMENT %s" % el)
                for k in range(attr_count):
                    ao = base + attr_start + k * attr_size
                    ans, aname, araw, asize, ares0, atype, adata = \
                        struct.unpack_from("<IIIHBBI", buf, ao)
                    # attribute resource id from the resource map
                    amap = resmap[aname] if aname < len(resmap) else 0
                    raw_s = strings[araw] if 0 <= araw < len(strings) else None
                    name_s = strings[aname] if aname < len(strings) else "?"
                    out_lines.append(
                        "  ATTR %-24s id=0x%08x type=0x%02x data=0x%08x raw=%r"
                        % (name_s, amap, atype, adata, raw_s))
        off += csize
    for ln in out_lines:
        print(ln)


if __name__ == "__main__":
    dump(sys.argv[1], sys.argv[2])
