#!/usr/bin/env python3
"""cont156_holder_xref.py — F-NEW-481 lever question: who STORES <type> instances?
Usage: cont156_holder_xref.py [apk] [type-desc like LLoz0;]
Scans classes*.dex. Resolves field_ids (per-list restart law, cont153 walker laws).
Reports:
  1. holder fields: every field whose DECLARED TYPE == <type>
  2. write sites: every iput-object/sput-object referencing those field_ids
  3. creation sites: every new-instance of <type>
"""
import struct, zipfile, sys

APK = sys.argv[1] if len(sys.argv) > 1 else 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
TARGET = sys.argv[2] if len(sys.argv) > 2 else 'Loz0;'

zf = zipfile.ZipFile(APK)
DEXES = sorted(n for n in zf.namelist() if n.startswith('classes') and n.endswith('.dex'))

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1; r |= (x & 0x7f) << s
        if not (x & 0x80): break
        s += 7
    return r, o

IPUT_OBJ = 0x5b; SPUT_OBJ = 0x69; NEW_INSTANCE = 0x22
IGET_OBJ = 0x54
# invoke-direct/range cover <init> calls (0x70 invoke-direct, 0x78 invoke-direct/range)
INVOKE_INIT_OPS = {0x70, 0x78}

SIZES = [2]*256
for _op in range(0x00, 0x08): SIZES[_op] = 1
SIZES[0x0f]=1; SIZES[0x10]=1; SIZES[0x11]=1; SIZES[0x12]=1
SIZES[0x08]=2; SIZES[0x09]=2; SIZES[0x0a]=1; SIZES[0x0e]=1
SIZES[0x0b]=1; SIZES[0x0c]=1; SIZES[0x0d]=1
SIZES[0x1d]=1; SIZES[0x1e]=1; SIZES[0x21]=1; SIZES[0x27]=1; SIZES[0x28]=1
for _op in range(0x7b, 0x90): SIZES[_op] = 1
for _op in range(0xb0, 0xd0): SIZES[_op] = 1
SIZES[0x13]=2; SIZES[0x15]=2; SIZES[0x16]=2; SIZES[0x19]=2
SIZES[0x14]=3; SIZES[0x18]=5
for _op in range(0x38,0x3e): SIZES[_op]=2
SIZES[0x1a]=2; SIZES[0x1c]=2; SIZES[0x1f]=2; SIZES[0x20]=2
SIZES[0x22]=2; SIZES[0x23]=2
SIZES[0x17]=3; SIZES[0x1b]=3
SIZES[0x24]=3; SIZES[0x25]=3; SIZES[0x26]=3
SIZES[0x29]=2; SIZES[0x2a]=3; SIZES[0x2b]=3; SIZES[0x2c]=3
for _op in range(0x2d,0x32): SIZES[_op]=2
for _op in range(0x44,0x52): SIZES[_op]=2
for _op in range(0x52,0x5e): SIZES[_op]=2
SIZES[0x5e]=2; SIZES[0x5f]=2
for _op in range(0x60,0x6e): SIZES[_op]=2
for _op in range(0x6e,0x73): SIZES[_op]=3
for _op in range(0x74,0x79): SIZES[_op]=3
for _op in range(0x90,0xb0): SIZES[_op]=2
for _op in range(0xd0,0xe3): SIZES[_op]=2
SIZES[0xfa]=4; SIZES[0xfb]=4
SIZES[0xfc]=3; SIZES[0xfd]=3; SIZES[0xfe]=3; SIZES[0xff]=3

grand_holders = {}; grand_writes = []; grand_news = []
# F-NEW-481 holder hunt: after new-instance TARGET, find the FIRST iput-object
# of the SAME register within the method (window 120 units) — the store target
# field identifies the holder even when R8 collapsed the declared type.
def track_store(dex, cstart, pc_new, isz, vreg):
    k = pc_new // 2 + 1
    seen = []
    steps = 0
    while k < isz and steps < 120:
        pc = k * 2
        op = dex[cstart + pc]
        sz = SIZES[op] if SIZES[op] else 1
        if op == 0x5b:  # iput-object
            vA = (dex[cstart + pc + 1] >> 4) & 0xf
            if vA == vreg:
                fidx = struct.unpack_from('<H', dex, cstart + pc + 2)[0]
                seen.append((pc, fidx))
                if len(seen) >= 3: break
        elif op in (0x07, 0x08, 0x09):  # move-object family — follow renames
            pass
        elif op == 0x11 and steps > 4:  # return-object — stop after reasonable window
            break
        k += sz; steps += 1
    return seen
for dn in DEXES:
    dex = zf.read(dn)
    str_size, str_off = struct.unpack_from('<2I', dex, 0x38)
    type_size, type_off = struct.unpack_from('<2I', dex, 0x40)
    fsize, foff = struct.unpack_from('<2I', dex, 0x50)
    meth_size, meth_off = struct.unpack_from('<2I', dex, 0x58)
    class_size, class_off = struct.unpack_from('<2I', dex, 0x60)
    soa = struct.unpack_from(f'<{str_size}I', dex, str_off)
    def str_at(si):
        off = soa[si]; _, o = uleb(dex, off)
        return dex[o:dex.index(b'\x00', o)].decode('utf-8', 'replace')
    tds = [str_at(struct.unpack_from('<I', dex, type_off + t*4)[0]) for t in range(type_size)]
    # field_id: (class_idx u2, type_idx u2, name_idx u4)
    fids = [(tds[c], tds[t], str_at(n)) for c, t, n in
            (struct.unpack_from('<HHI', dex, foff + i*8) for i in range(fsize))]
    mids = [(tds[c], str_at(n)) for c, _, n in
            (struct.unpack_from('<HHI', dex, meth_off + i*8) for i in range(meth_size))]
    holder_fids = {i for i, (c, t, n) in enumerate(fids) if t == TARGET}
    for i in holder_fids:
        c, t, n = fids[i]
        grand_holders.setdefault((c, n), []).append(dn)
    # NOTE: walk runs even when holder_fids is empty — creation sites matter
    # even with zero typed holders (R8 generic-collapse law).
    for ci in range(class_size):
        cdef = class_off + ci*32
        cls_desc = tds[struct.unpack_from('<H', dex, cdef)[0]]
        coff = struct.unpack_from('<I', dex, cdef + 24)[0]
        if coff == 0: continue
        o = coff
        sf, o = uleb(dex, o)
        ifc, o = uleb(dex, o)
        dm_s, o = uleb(dex, o)
        dm_i, o = uleb(dex, o)
        for _ in range(sf):
            _, o = uleb(dex, o); _, o = uleb(dex, o)
        for _ in range(ifc):
            _, o = uleb(dex, o); _, o = uleb(dex, o)
        METHS = []
        for cnt in (dm_s, dm_i):
            prev = 0
            for _ in range(cnt):
                mdiff, o = uleb(dex, o)
                midx = prev + mdiff
                prev = midx
                acc, o = uleb(dex, o)
                codeoff, o = uleb(dex, o)
                if codeoff == 0: continue
                mname = mids[midx][1] if midx < len(mids) else '?'
                METHS.append((mname, codeoff))
        for mname, codeoff in METHS:
            regs, ins, outs, tries, dbg, isz = struct.unpack_from('<4HII', dex, codeoff)
            cstart = codeoff + 16
            k = 0
            while k < isz:
                pc = k * 2
                op = dex[cstart + pc]
                sz = SIZES[op] if SIZES[op] else 1
                if op == NEW_INSTANCE:
                    tidx = struct.unpack_from('<H', dex, cstart + pc + 2)[0]
                    if tidx < len(tds) and tds[tidx] == TARGET:
                        vA = dex[cstart + pc + 1] & 0xf
                        stores = track_store(dex, cstart, pc, isz, vA)
                        sdesc = []
                        for spc, sfidx in stores:
                            if sfidx < len(fids):
                                fc, ft, fn = fids[sfidx]
                                sdesc.append(f'pc={spc}->{fc}.{fn}:{ft}')
                            else:
                                sdesc.append(f'pc={spc}->fid{sfidx}')
                        grand_news.append(f'{cls_desc}.{mname} pc={pc} new-instance {TARGET} stores=[{"; ".join(sdesc) or "NO-STORE-IN-WINDOW"}]')
                elif op in INVOKE_INIT_OPS:
                    mref = struct.unpack_from('<H', dex, cstart + pc + 2)[0]
                    if mref < len(mids) and mids[mref][0] == TARGET and mids[mref][1] == '<init>':
                        grand_news.append(f'{cls_desc}.{mname} pc={pc} invoke-init {TARGET}.<init>')
                elif op in (IPUT_OBJ, SPUT_OBJ):
                    fidx = struct.unpack_from('<H', dex, cstart + pc + 2)[0]
                    if fidx in holder_fids:
                        fc, ft, fn = fids[fidx]
                        w = 'iput' if op == IPUT_OBJ else 'sput'
                        grand_writes.append(f'{cls_desc}.{mname} pc={pc} {w}-object {fc}.{fn} (fld type {ft})')
                k += sz

print(f'=== HOLDER FIELDS with declared type {TARGET} ===')
for (c, n), dnames in sorted(grand_holders.items()):
    print(f'  {c} . {n}   [{dnames[0]}]')
print(f'=== WRITE SITES (iput/sput-object into holder fields) ===')
for w in grand_writes:
    print(f'  {w}')
print(f'=== CREATION SITES (new-instance {TARGET}) ===')
for w in grand_news:
    print(f'  {w}')
print(f'totals: holders={len(grand_holders)} writes={len(grand_writes)} news={len(grand_news)}')
