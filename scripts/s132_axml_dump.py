#!/usr/bin/env python3
"""s132_axml_dump.py — minimal self-contained binary AXML decoder.
Usage: s132_axml_dump.py <apk> <entry>  (prints indented element tree with attrs)
S132 Wave-1 source-first investigation: decode opencalculator's REAL
activity_main layout to identify the exact container classes + children.
"""
import struct
import sys
import zipfile


def parse_string_pool(buf, off):
    (typ, hsz, size, count, stylecount, flags, sstart, estart) = struct.unpack_from(
        "<HHIIIIII", buf, off)
    utf8 = flags & (1 << 8)
    offs = struct.unpack_from("<%dI" % count, buf, off + hsz)
    strs = []
    for o in offs:
        p = off + sstart + o
        if utf8:
            # u16len, u8len, bytes
            def dec_len(p, is8):
                b = buf[p]
                if b & 0x80:
                    return ((b & 0x7F) << 8) | buf[p + 1], p + 2
                return b, p + 1
            _, p2 = dec_len(p, False)
            n, _ = dec_len(p2, True)
            if n & 0x80:
                n = ((n & 0x7F) << 8) | buf[p2 + 2]
            # recompute: first len is u16 chars, second is utf8 bytes
            l16, q = dec_len(p, False)
            l8, q2 = dec_len(q, True)
            s = buf[q2:q2 + l8].decode("utf-8", "replace")
            strs.append(s)
        else:
            (n,) = struct.unpack_from("<H", buf, p)
            if n & 0x8000:
                (n2,) = struct.unpack_from("<H", buf, p + 2)
                n = ((n & 0x7FFF) << 16) | n2
                p += 4
            else:
                p += 2
            strs.append(buf[p:p + n * 2].decode("utf-16-le", "replace"))
    return strs


def dim(v):
    # AOSP complex dimension: unit = v&0xF, radix=(v>>4)&3, signed mantissa = v>>8 (24-bit)
    m = (v >> 8) & 0xFFFFFF
    if m & 0x800000:
        m -= 1 << 24
    f = m / (256.0 * (256.0 ** ((v >> 4) & 3)))
    units = ["px", "dip", "sp", "pt", "in", "mm"]
    return "%g%s" % (f, units[v & 0xF] if (v & 0xF) < len(units) else "?")


def main():
    apk, entry = sys.argv[1], sys.argv[2]
    z = zipfile.ZipFile(apk)
    buf = z.read(entry)
    # top chunk
    (typ, hsz, size) = struct.unpack_from("<HHI", buf, 0)
    off = hsz
    strs = []
    resmap = []
    # walk chunks
    while off < len(buf):
        (t, h, s) = struct.unpack_from("<HHI", buf, off)
        if t == 0x0001:  # string pool
            strs = parse_string_pool(buf, off)
        elif t == 0x0180:  # res map
            n = (s - h) // 4
            resmap = list(struct.unpack_from("<%dI" % n, buf, off + h))
        elif t == 0x0102:  # start element
            # node header = {type,headerSize,size} + lineNumber + comment = 16 bytes
            # ResXMLTree_attrExt: ns,name,attributeStart,attributeSize,attributeCount,idIndex,classIndex,styleIndex
            (_ns, name, astart, _asz, ac) = struct.unpack_from("<IIHHH", buf, off + 16)
            p = off + 16 + astart
            out = []
            for i in range(ac):
                # ResXMLTree_attribute = {ns,name,rawValue} + Res_value{size:u16,res0:u8,type:u8,data:u32}
                (ans, aname, araw, _asz, _r0, atype, adata) = struct.unpack_from(
                    "<IIIHBBI", buf, p)
                p += 20
                aname_s = strs[aname] if aname < len(strs) else "?"
                araw_s = strs[araw] if araw != 0xFFFFFFFF and araw < len(strs) else None
                if araw_s is not None:
                    val = araw_s
                elif atype == 0x10:
                    val = str(adata if adata < 0x80000000 else adata - (1 << 32))
                elif atype == 0x04:
                    val = "%.4f" % struct.unpack("<f", struct.pack("<I", adata))[0]
                elif atype == 0x12:
                    val = "true" if adata else "false"
                elif atype == 0x05:
                    val = dim(adata)
                elif atype == 0x01 and adata >> 24 == 0x01:
                    val = "@android:0x%08x" % adata
                elif atype == 0x01:
                    val = "@0x%08x" % adata
                elif atype == 0x02:
                    val = "?0x%08x" % adata
                elif atype in (0x1c, 0x1d, 0x1e, 0x1f):
                    val = "#%08x" % adata
                else:
                    val = "%d(0x%x)" % (adata, adata)
                out.append("%s=%s" % (aname_s, val))
            en = strs[name] if name < len(strs) else "?"
            print("  " * 0 + "<%s %s>" % (en, " ".join(out)))
        off += s


if __name__ == "__main__":
    main()
