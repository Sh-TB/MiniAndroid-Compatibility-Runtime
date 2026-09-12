#!/usr/bin/env python3
"""
scripts/forensic/m3_35c_layout_probe.py — settle the 35c/3rc index-unit placement law.

HYP-A (AOSP dex-format spec):  Ag|op, FEDC, BBBB@idx3
HYP-B (alternate):             Ag|op, BBBB@idx2, FEDC

For every invoke instruction in classes.dex decode both ways and count:
  * out-of-range method ids
  * invoke-static/invoke-direct on methods whose declaring class is a
    known framework class AND whose call site encodes regs that cannot
    type-check (we only use the cheap, decisive proxy: framework classes
    where VIRTUAL dispatch is mandatory, e.g. Intent.putExtra, TextView.setText)
The interpretation with fewer contradictions wins.
"""
import struct, zipfile, sys

KNOWN_VIRTUAL = {  # framework methods that can NEVER be invoke-static
    "putExtra", "setText", "setOnClickListener", "findViewById",
    "getBroadcastItem", "put", "add", "get", "postDelayed", "removeCallbacks",
    "startActivity", "onCreate", "toString", "equals", "hashCode",
}


def main():
    apk = sys.argv[1]
    z = zipfile.ZipFile(apk)
    d = z.read("classes.dex")
    u4 = lambda o: struct.unpack_from("<I", d, o)[0]
    u2 = lambda o: struct.unpack_from("<H", d, o)[0]
    str_off, m_off, type_off = u4(0x3C), u4(0x5C), u4(0x44)
    s_sz, m_sz = u4(0x38), u4(0x58)
    c_off, c_sz = u4(0x64), u4(0x60)

    def uleb(p):
        r = 0; s = 0
        while True:
            b = d[p + s]; r |= (b & 0x7f) << (7 * s); s += 1
            if not (b & 0x80):
                return r, p + s

    def gs(idx):
        off = u4(str_off + 4 * idx); r, p = uleb(off)
        return d[p:p + r].split(b"\x00")[0].decode("utf-8", "replace")

    def ty(idx):
        return gs(u4(type_off + 4 * idx))

    def meth_name(mi):
        if mi >= m_sz:
            return None
        return gs(u4(m_off + 8 * mi + 4))

    stat = {"A": {"oob": 0, "static_virt": 0, "total": 0},
            "B": {"oob": 0, "static_virt": 0, "total": 0}}
    examples = []
    for i in range(c_sz):
        off = c_off + 32 * i
        cdo = u4(off + 24)
        if not cdo:
            continue
        p = cdo
        sf, p = uleb(p); iff, p = uleb(p); dm, p = uleb(p); vm, p = uleb(p)
        for _ in range(sf + iff):
            _, p = uleb(p); _, p = uleb(p)
        for n_meth, restart in ((dm, True), (vm, False)):
            mi = 0
            for _ in range(n_meth):
                d1, p = uleb(p); d2, p = uleb(p); d3, p = uleb(p)
                mi = d1 if restart else mi + d1
                if not d3:
                    continue
                isz = u4(d3 + 12)
                code = d3 + 16
                pc = 0
                while pc < isz:
                    w = u2(code + 2 * pc)
                    op = w & 0xff
                    if op in (0x60, 0x61, 0x62, 0x63, 0x64) or \
                       op in (0x74, 0x75, 0x76, 0x77, 0x78):
                        is_range = op >= 0x74
                        if is_range:
                            idx2 = u2(code + 2 * pc + 2)
                            idx3 = u2(code + 2 * pc + 4)
                        else:
                            idx2 = u2(code + 2 * pc + 2)
                            idx3 = u2(code + 2 * pc + 4)
                            # NOTE: FEDC occupies unit2, BBBB unit3 per spec;
                            # swapped hyp reads idx from unit2.
                        for hyp, midx in (("A", idx3), ("B", idx2)):
                            stat[hyp]["total"] += 1
                            if midx >= m_sz:
                                stat[hyp]["oob"] += 1
                                continue
                            name = meth_name(midx)
                            if op in (0x62, 0x63, 0x76, 0x77) and name in KNOWN_VIRTUAL:
                                # static/direct call to a mandatory-virtual
                                # framework method = contradiction
                                stat[hyp]["static_virt"] += 1
                                if len(examples) < 12:
                                    examples.append(
                                        (hyp, hex(pc), op, midx, name))
                    # advance by format size (coarse: invokes are 3 units)
                    if op in (0x60, 0x61, 0x62, 0x63, 0x64,
                              0x74, 0x75, 0x76, 0x77, 0x78):
                        pc += 3
                    else:
                        pc += _opsize(op)
    for hyp in ("A", "B"):
        print(f"HYP-{hyp}: total={stat[hyp]['total']} oob={stat[hyp]['oob']} "
              f"static-on-virtual={stat[hyp]['static_virt']}")
    for e in examples:
        print("  example", e)


_OP_SIZES = None


def _opsize(op):
    """Coarse size table (units) — enough to keep alignment for the scan."""
    global _OP_SIZES
    if _OP_SIZES is None:
        _OP_SIZES = {}
        one = set(range(0x00, 0x0c)) | {0x0d} | set(range(0x1d, 0x28))
        one = {0x00, 0x01, 0x04, 0x07, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
               0x10, 0x11, 0x12, 0x1b - 0x1b} | {
            0x1d, 0x1e, 0x21, 0x27, 0x28, 0x7b} | set(range(0x7b, 0x90)) | \
            set(range(0xb0, 0xc8))
        two = {0x02, 0x05, 0x08, 0x13, 0x15, 0x16, 0x19, 0x1a, 0x1c, 0x1f,
               0x20, 0x22, 0x23, 0x29, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36,
               0x37, 0x38, 0x39, 0x3a, 0x3b, 0x3c, 0x3d} | \
            set(range(0x44, 0x60)) | set(range(0x90, 0xa0)) | \
            set(range(0xd0, 0xe6))
        three = {0x03, 0x06, 0x09, 0x14, 0x17, 0x18, 0x24, 0x25, 0x26, 0x2a,
                 0x2b, 0x2c, 0x2d, 0x2e, 0x2f, 0x30} | \
            set(range(0x60, 0x7b)) - set(range(0x60, 0x60))
        for o in range(0x100):
            if o in one:
                _OP_SIZES[o] = 1
            elif o in two:
                _OP_SIZES[o] = 2
            elif o in three or o in (0x60, 0x61, 0x62, 0x63, 0x64, 0x65,
                                     0x66, 0x67, 0x68, 0x69):
                _OP_SIZES[o] = 3
            elif o in (0x18, 0x1b):
                _OP_SIZES[o] = 3
            else:
                _OP_SIZES[o] = 1
        # payloads
        _OP_SIZES[0x00] = 1
        # high-priority corrections
        for o in (0x60, 0x61, 0x62, 0x63, 0x64, 0x74, 0x75, 0x76, 0x77, 0x78):
            _OP_SIZES[o] = 3
        for o in range(0x65, 0x74):
            _OP_SIZES[o] = 3
        for o in range(0x7b, 0x90):
            _OP_SIZES[o] = 1
        for o in range(0x90, 0xb0):
            _OP_SIZES[o] = 2
        for o in range(0xb0, 0xd0):
            _OP_SIZES[o] = 1
    return _OP_SIZES.get(op, 1)


if __name__ == "__main__":
    main()
