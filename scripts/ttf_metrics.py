#!/usr/bin/env python3
"""
ttf_metrics.py — parse TTF/OTF vertical metric tables (head/hhea/OS-2/post)
with stdlib only. G32/G36 evidence: unitsPerEm, hhea ascender/descender/
lineGap, OS/2 winAscent/winDescent/typo metrics + fsSelection USE_TYPO bit,
and the advance width of a codepoint from hmtx (monospace check).
"""
import struct
import sys


def main(path, probes=()):
    with open(path, "rb") as f:
        data = f.read()
    tag_count = struct.unpack_from(">H", data, 4)[0]
    tables = {}
    for i in range(tag_count):
        off = 12 + i * 16
        tag = data[off:off + 4].decode("latin1")
        toff, tlen = struct.unpack_from(">II", data, off + 8)
        tables[tag] = (toff, tlen)
    upem, = struct.unpack_from(">H", data, tables["head"][0] + 18)
    ho = tables["hhea"][0]
    asc, desc, gap = struct.unpack_from(">hhh", data, ho + 4)
    print("unitsPerEm      :", upem)
    print("hhea.ascender   : %d  (%.5f em)" % (asc, asc / upem))
    print("hhea.descender  : %d  (%.5f em)" % (desc, desc / upem))
    print("hhea.lineGap    : %d  (%.5f em)" % (gap, gap / upem))
    if "OS/2" in tables:
        o = tables["OS/2"][0]
        version, = struct.unpack_from(">H", data, o)
        winAsc, winDesc = struct.unpack_from(">HH", data, o + 74)
        print("OS/2.version    :", version)
        print("usWinAscent     : %d  (%.5f em)" % (winAsc, winAsc / upem))
        print("usWinDescent    : %d  (%.5f em)" % (winDesc, winDesc / upem))
        fsSel, = struct.unpack_from(">H", data, o + 62)
        print("fsSelection     : 0x%04x  USE_TYPO_METRICS=%s"
              % (fsSel, bool(fsSel & 0x80)))
        if version >= 2:
            tAsc, tDesc, tGap = struct.unpack_from(">hhh", data, o + 68)
            print("sTypoAscender   : %d  (%.5f em)" % (tAsc, tAsc / upem))
            print("sTypoDescender  : %d  (%.5f em)" % (tDesc, tDesc / upem))
            print("sTypoLineGap    : %d  (%.5f em)" % (tGap, tGap / upem))
    # glyph metrics
    num_glyphs, = struct.unpack_from(">H", data, tables["maxp"][0] + 4)
    print("numGlyphs       :", num_glyphs)
    lo, hi = struct.unpack_from(">HH", data, tables["cmap"][0] + 4)
    # find format-4 subtable (first subtable), monospace fonts have simple maps
    co = tables["cmap"][0]
    n, = struct.unpack_from(">H", data, co + 2)
    sub4 = None
    for i in range(n):
        pid, eid, soff = struct.unpack_from(">HHI", data, co + 4 + i * 8)
        fmt, = struct.unpack_from(">H", data, co + soff)
        if fmt in (4, 12):
            sub4 = (co + soff, fmt)
    if sub4 and probes:
        so, fmt = sub4
        hmtx = tables["hmtx"][0]

        def glyph_index(cp):
            if fmt == 4:
                segX2, = struct.unpack_from(">H", data, so + 6)
                seg = segX2 // 2
                ends = struct.unpack_from(">%dH" % seg, data, so + 14)
                starts = struct.unpack_from(">%dH" % seg, data, so + 16 + segX2)
                deltas = struct.unpack_from(">%dh" % seg, data, so + 16 + segX2 * 2)
                rng_off_base = so + 16 + segX2 * 3
                rng = struct.unpack_from(">%dH" % seg, data, rng_off_base)
                for i in range(seg):
                    if starts[i] <= cp <= ends[i]:
                        if rng[i] == 0:
                            return (cp + deltas[i]) & 0xFFFF
                        gi_off = rng_off_base + i * 2 + rng[i] + (cp - starts[i]) * 2
                        gi, = struct.unpack_from(">H", data, gi_off)
                        return (gi + deltas[i]) & 0xFFFF if gi else 0
                return 0
            return 0

        def advance(gi):
            aw, = struct.unpack_from(">H", data, hmtx + gi * 4)
            lsb, = struct.unpack_from(">h", data, hmtx + gi * 4 + 2)
            return aw, lsb

        for ch in sys.argv[2]:
            cp = ord(ch)
            gi = glyph_index(cp)
            if gi:
                aw, lsb = advance(gi)
                print("U+%04X %r gid=%3d advance=%d (%.5f em) lsb=%d"
                      % (cp, ch, gi, aw, aw / upem, lsb))
            else:
                print("U+%04X %r NOT IN FONT" % (cp, ch))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
