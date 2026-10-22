#!/usr/bin/env python3
"""cont155_methxref.py — invoke-site xref for one method: who calls <class>.<name>?
Usage: cont155_methxref.py [apk] [class-desc like Lel0;] [method-name like i]
Defaults: dooz v23, Lel0;, i. Scans classes*.dex, all invoke-* opcodes (0x6e-0x72
+ 0x74-0x78), resolves method_id via index (per-list restart law, cont153).
Prints: caller_class.caller_method idx -> target; plus iget/iput sites of
<class> fields named in FIELD_WATCH (below) when WATCH_FIELDS=1."""
import struct, zipfile, sys, os

APK = sys.argv[1] if len(sys.argv) > 1 else 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
CLS = sys.argv[2] if len(sys.argv) > 2 else 'Lel0;'
METH = sys.argv[3] if len(sys.argv) > 3 else 'i'

zf = zipfile.ZipFile(APK)
DEXES = sorted(n for n in zf.namelist() if n.startswith('classes') and n.endswith('.dex'))

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1; r |= (x & 0x7f) << s
        if not (x & 0x80): break
        s += 7
    return r, o

INVOKE_OPS = set(range(0x6e, 0x73)) | set(range(0x74, 0x79))
UNITS = {op: 3 for op in INVOKE_OPS}
# SIZES law — ported VERBATIM from verified cont151_disasm_regs.py (instruction-aligned stepping)
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

total_sites = 0
for dn in DEXES:
    dex = zf.read(dn)
    str_size, str_off = struct.unpack_from('<2I', dex, 0x38)
    type_size, type_off = struct.unpack_from('<2I', dex, 0x40)
    meth_size, meth_off = struct.unpack_from('<2I', dex, 0x58)
    class_size, class_off = struct.unpack_from('<2I', dex, 0x60)
    soa = struct.unpack_from(f'<{str_size}I', dex, str_off)
    def str_at(si):
        off = soa[si]; _, o = uleb(dex, off)
        return dex[o:dex.index(b'\x00', o)].decode('utf-8', 'replace')
    tds = [str_at(struct.unpack_from('<I', dex, type_off + t*4)[0]) for t in range(type_size)]
    mids = [(tds[c], str_at(n)) for c, _, n in
            (struct.unpack_from('<HHI', dex, meth_off + i*8) for i in range(meth_size))]
    targets = {i for i in range(meth_size) if mids[i] == (CLS, METH)}
    if not targets:
        print(f'{dn}: no method_id {CLS}.{METH}')
        continue
    print(f'{dn}: {CLS}.{METH} method_ids at {[f"mid{i}" for i in targets]}')
    # walk classes (class_def = 32 bytes; class_data_off at +24)
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
        for _ in range(sf + ifc):
            _, o = uleb(dex, o); _, o = uleb(dex, o)  # field entries skip (fields before methods)
        # cont153 VERIFIED LAW: method_idx diff chain RESTARTS per list (direct/virtual)
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
            # instruction-ALIGNED walk (SIZES law ported from verified cont151_disasm_regs)
            k = 0
            while k < isz:
                pc = k * 2
                op = dex[cstart + pc]  # opcode = LOW byte of little-endian unit (cont151 law)
                sz = SIZES[op] if SIZES[op] else 1
                if op in UNITS:
                    mref = struct.unpack_from('<H', dex, cstart + pc + 2)[0]
                    if mref in targets:
                        print(f'  CALL: {cls_desc}.{mname} pc={pc} op=0x{op:02x}')
                        total_sites += 1
                k += sz
print(f'total invoke sites: {total_sites}')
