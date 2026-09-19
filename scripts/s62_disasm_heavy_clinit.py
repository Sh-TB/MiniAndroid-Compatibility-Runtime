#!/usr/bin/env python3
"""S62 R-NEW-381: disassemble the heaviest <clinit> chains from dooz v23.
Targets (from s62_clinit_costs.py): Lug0; (23 ins -> 7.1s), Lqk; (117 -> 6.3s),
Lbl; (1004 -> 6.3s), Lv52; (5 -> 1.4s), Lkb; (3 -> 0.7s), Ls02; (475 -> 3.6s).
Usage: python3 s62_disasm_heavy_clinit.py [dooz_23|dooz_18]
"""
import struct, sys, zipfile

APKS = {
    'dooz_23': '/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk',
    'dooz_18': '/home/z/my-project/apk_cache/io.github.yamin8000.dooz_18.apk',
}
TARGETS = ['Lug0;', 'Lqk;', 'Lbl;', 'Lv52;', 'Lkb;', 'Ls02;']

dexpath = sys.argv[1] if len(sys.argv) > 1 else 'dooz_23'
z = zipfile.ZipFile(APKS[dexpath])
dexnames = [n for n in z.namelist() if n.endswith('.dex')]


def uleb(buf, off):
    r = 0
    s = 0
    while True:
        b = buf[off]
        off += 1
        r |= (b & 0x7f) << s
        if not (b & 0x80):
            break
        s += 7
    return r, off


def load(dn):
    d = z.read(dn)
    ssz, sof = struct.unpack_from('<II', d, 0x38)
    tsz, tof = struct.unpack_from('<II', d, 0x40)
    psz, pof = struct.unpack_from('<II', d, 0x48)
    fsz, fof = struct.unpack_from('<II', d, 0x50)
    msz, mof = struct.unpack_from('<II', d, 0x58)
    cds, cdo = struct.unpack_from('<II', d, 0x60)
    strs = []
    for i in range(ssz):
        off = struct.unpack_from('<I', d, sof + 4 * i)[0]
        n, p = uleb(d, off)
        strs.append(d[p:p + n].decode('utf-8', 'replace'))
    types = [strs[struct.unpack_from('<I', d, tof + 4 * i)[0]]
             for i in range(tsz)]
    protos = []
    for i in range(psz):
        so = pof + 12 * i
        si, ri, poff = struct.unpack_from('<III', d, so)
        params = []
        if poff:
            nparams = struct.unpack_from('<I', d, poff)[0]
            for j in range(nparams):
                params.append(types[struct.unpack_from(
                    '<H', d, poff + 4 + 2 * j)[0]])
        protos.append((strs[si], types[ri], params))
    methods = []
    for i in range(msz):
        ci, pi, ni = struct.unpack_from('<HHI', d, mof + 8 * i)
        methods.append((types[ci], protos[pi], strs[ni]))
    classes = []
    for i in range(cds):
        so = cdo + 32 * i
        cidx = struct.unpack_from('<I', d, so)[0]
        sup = struct.unpack_from('<I', d, so + 8)[0]
        coff = struct.unpack_from('<I', d, so + 24)[0]
        classes.append((types[cidx],
                        types[sup] if sup != 0xFFFFFFFF else None, coff))
    return d, strs, methods, classes


def class_data(d, coff):
    if coff == 0:
        return [], [], [], []
    p = coff
    out = []
    for _sec in range(4):
        n, p = uleb(d, p)
        idx = 0
        entries = []
        for _ in range(n):
            idx += uleb(d, p)[0]
            p = uleb(d, p)[1]
            acc, p = uleb(d, p)
            if _sec >= 2:
                coff2, p = uleb(d, p)
                entries.append((idx, coff2))
            else:
                entries.append((idx, acc))
        out.append(entries)
    return out[0], out[1], out[2], out[3]


def code_item(d, off):
    if off == 0:
        return None
    rs, ins, outs, tries, dbg, insns_sz, insns_off = struct.unpack_from(
        '<HHHHIII', d, off)
    return insns_sz, insns_off


OPCODES = {
    0x00: 'nop', 0x01: 'move', 0x02: 'move/from16', 0x04: 'move-wide',
    0x07: 'move-object', 0x0a: 'move-result', 0x0b: 'move-result-wide',
    0x0c: 'move-result-object', 0x0d: 'move-exception', 0x0e: 'return-void',
    0x0f: 'return', 0x10: 'return-wide', 0x11: 'return-object',
    0x12: 'const/4', 0x13: 'const/16', 0x14: 'const', 0x15: 'const/high16',
    0x16: 'const-wide/16', 0x1a: 'const-string', 0x1c: 'const-class',
    0x1f: 'check-cast', 0x20: 'instance-of', 0x21: 'array-length',
    0x22: 'new-instance', 0x23: 'new-array', 0x24: 'filled-new-array',
    0x26: 'fill-array-data', 0x27: 'throw', 0x28: 'goto', 0x29: 'goto/16',
    0x2b: 'packed-switch', 0x2c: 'sparse-switch', 0x44: 'aget', 0x4b: 'aput',
    0x4f: 'iget', 0x52: 'iget', 0x54: 'iget-object', 0x55: 'iget-wide',
    0x59: 'iput', 0x5b: 'iput-object', 0x5f: 'iput-boolean', 0x60: 'sget',
    0x61: 'sget-wide', 0x62: 'sget-object', 0x63: 'sget-boolean',
    0x64: 'sget-byte', 0x69: 'sput', 0x6a: 'sput-wide', 0x6b: 'sput-object',
    0x6e: 'invoke-virtual', 0x6f: 'invoke-super', 0x70: 'invoke-static',
    0x71: 'invoke-interface', 0x74: 'invoke-virtual/range',
    0x77: 'invoke-static/range', 0x78: 'invoke-interface/range',
    0x90: 'add-int', 0x91: 'sub-int', 0x92: 'mul-int', 0x93: 'div-int',
    0x9f: 'add-long', 0xa0: 'sub-long', 0xa3: 'mul-long', 0xaf: 'add-double',
    0xb0: 'add-int/2addr', 0xb1: 'sub-int/2addr', 0xb2: 'mul-int/2addr',
    0xbb: 'add-long/2addr', 0xbd: 'mul-long/2addr', 0xcd: 'add-double/2addr',
    0xd0: 'add-int/lit16', 0xd8: 'add-int/lit8', 0xda: 'sub-int/lit8',
    0xdb: 'mul-int/lit8', 0xdc: 'div-int/lit8', 0xe0: 'add-long/lit8',
}

IDX_21C = (0x1a, 0x1b, 0x1c, 0x1f, 0x20, 0x22, 0x23, 0x24, 0x60, 0x61, 0x62,
           0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6a, 0x6b, 0x6c, 0x6d)
IDX_35C = (0x6e, 0x6f, 0x70, 0x71, 0x72)

for dn in dexnames:
    d, strs, methods, classes = load(dn)
    found = {}
    for cname, sup, coff in classes:
        if cname not in TARGETS:
            continue
        sf_i, inf_i, dm_i, vm_i = class_data(d, coff)
        for mi, mcoff in dm_i + vm_i:
            if mi >= len(methods):
                print('!! bad method idx', mi, 'in', cname)
                continue
            mcls, proto, mname = methods[mi]
            if mcls == cname and mname == '<clinit>' and mcoff:
                found[cname] = (sup, code_item(d, mcoff))
    for t in TARGETS:
        if t not in found:
            continue
        sup, ci_item = found[t]
        if not ci_item:
            continue
        insns_sz, insns_off = ci_item
        print('== %s  super=%s  insns=%d units ==' % (t, sup, insns_sz))
        p = insns_off * 2
        end = p + insns_sz * 2
        while p < end - 1:
            op = d[p + 1]
            hi = d[p]
            name = OPCODES.get(op, 'op=0x%02x' % op)
            if op == 0x1a:
                idx = struct.unpack_from('<H', d, p + 2)[0]
                s = strs[idx]
                print('  %04d %-16s v%d, "%s" (len=%d)' % (
                    (p - insns_off * 2) // 2, name, hi, s[:50], len(s)))
                p += 4
                continue
            if op in IDX_35C:
                midx = struct.unpack_from('<H', d, p + 2)[0]
                mc, proto, mn = methods[midx]
                print('  %04d %-16s %s.%s:%s' % (
                    (p - insns_off * 2) // 2, name, mc, mn, proto[1]))
                p += 6
                continue
            if op in IDX_21C:
                idx = struct.unpack_from('<H', d, p + 2)[0]
                if op in (0x1c, 0x1f, 0x20, 0x22, 0x23, 0x24):
                    extra = types_dump = idx and ''
                    # resolve type via type_ids not loaded; show string idx
                    extra = 'type_idx=%d' % idx
                else:
                    extra = 'field_idx=%d' % idx
                print('  %04d %-16s v%d, %s' % (
                    (p - insns_off * 2) // 2, name, hi, extra))
                p += 4
                continue
            if op == 0x28:
                print('  %04d goto %+d' % ((p - insns_off * 2) // 2,
                                           (hi ^ 0x80) - 0x80))
                p += 2
                continue
            width = 2
            if op in (0x02, 0x13, 0x15, 0x16, 0xd0, 0xd8, 0xda, 0xdb, 0xdc,
                      0xe0, 0x54, 0x52, 0x55, 0x5b, 0x59, 0x44, 0x4b):
                width = 4
            elif op in (0x14, 0x17, 0x18, 0x26, 0x2b, 0x2c):
                width = 6
            raw = d[p:p + width].hex()
            print('  %04d %-16s raw=%s' % ((p - insns_off * 2) // 2, name,
                                           raw))
            p += width
        print()
