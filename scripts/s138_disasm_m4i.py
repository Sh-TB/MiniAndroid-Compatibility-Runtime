#!/usr/bin/env python3
"""s138_disasm_m4i.py — disassemble Lm4;.i from the dooz DEX: list every
instance-of/check-cast instruction with its resolved type descriptor.
Decides what the materialize-family method ACTUALLY tests."""
import struct, zipfile, sys

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
CLS = sys.argv[1] if len(sys.argv) > 1 else 'Lm4;'
METHODS = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else {'i'}

def read_uleb(buf, off):
    r = 0; s = 0
    while True:
        b = buf[off]; off += 1
        r |= (b & 0x7F) << s
        if not (b & 0x80): break
        s += 7
    return r, off

z = zipfile.ZipFile(APK)
d = z.read('classes.dex')
string_ids_size, string_ids_off = struct.unpack_from('<II', d, 0x38)
type_ids_size, type_ids_off = struct.unpack_from('<II', d, 0x40)
proto_off = 0x48
field_ids_size, field_ids_off = struct.unpack_from('<II', d, 0x50)
method_ids_size, method_ids_off = struct.unpack_from('<II', d, 0x58)
class_defs_size, class_defs_off = struct.unpack_from('<II', d, 0x60)

def get_str(idx):
    off = struct.unpack_from('<I', d, string_ids_off + 4 * idx)[0]
    n, off = read_uleb(d, off)
    end = d.index(b'\x00', off)
    return d[off:end].decode('utf-8', 'replace')

def get_type(idx):
    if idx >= type_ids_size: return f'<type{idx}>'
    si = struct.unpack_from('<I', d, type_ids_off + 4 * idx)[0]
    return get_str(si)

def get_method(idx):
    if idx >= method_ids_size: return f'<method{idx}>'
    cls, proto, name = struct.unpack_from('<HHI', d, method_ids_off + 8 * idx)
    return f'{get_type(cls)}->{get_str(name)}'

found = False
for i in range(class_defs_size):
    off = class_defs_off + 32 * i
    class_idx, access, super_idx, ifaces_off, src, ann, cd_off, sval = struct.unpack_from('<IIIIIIII', d, off)
    if get_type(class_idx) != CLS: continue
    found = True
    if cd_off == 0:
        print('no class_data'); break
    p = cd_off
    sf, inf, dm, vm = read_uleb(d, p)[0], 0, 0, 0
    sf, p = read_uleb(d, p); inf, p = read_uleb(d, p)
    dm, p = read_uleb(d, p); vm, p = read_uleb(d, p)
    # skip static+instance fields
    for kind, cnt in (('sf', sf), ('inf', inf)):
        prev = 0
        for _ in range(cnt):
            di, p = read_uleb(d, p); ai, p = read_uleb(d, p)
            prev += di
    for _ in range(dm):  # direct methods
        mi, p = read_uleb(d, p); ai, p = read_uleb(d, p); ci, p = read_uleb(d, p)
        prev_m = mi
        name = get_str(struct.unpack_from('<I', d, method_ids_off + 8 * mi)[0 + 2] & 0xFFFFFFFF) if False else None
        # method index mi is absolute diff-encoded: recompute
        if _ == 0: midx = mi
        name = get_str(struct.unpack_from('<I', d, method_ids_off + 8 * midx + 4)[0]) if False else ''
        ci_off = None
    # simpler: re-walk direct+virtual collecting (midx, code_off)
    p = cd_off
    sf, p = read_uleb(d, p); inf, p = read_uleb(d, p)
    dm, p = read_uleb(d, p); vm, p = read_uleb(d, p)
    mlist = []
    for kind, cnt in ((0, sf), (1, inf)):
        prev = 0
        for _ in range(cnt):
            di, p = read_uleb(d, p); ai, p = read_uleb(d, p)
            prev += di
    for kind, cnt in ((0, dm), (1, vm)):
        prev = 0
        for _ in range(cnt):
            di, p = read_uleb(d, p); ai, p = read_uleb(d, p); ci, p = read_uleb(d, p)
            prev += di
            mlist.append((kind, prev, ai, ci))
    for kind, midx, acc, ci in mlist:
        mname = get_str(struct.unpack_from('<I', d, method_ids_off + 8 * midx + 4)[0])
        if METHODS is not None and mname not in METHODS: continue
        if ci == 0:
            print(f'method {mname}: abstract/native (no code)'); continue
        regs, ins, outs, tries, dbg, insns_size, insns_off = struct.unpack_from('<HHHHII I'.replace(' ',''), d, ci)
        print(f'== {CLS}->{mname} regs={regs} insns={insns_size} code_off={ci}')
        code = d[insns_off:insns_off + insns_size * 2]
        j = 0
        while j < insns_size:
            op = code[j * 2]
            if op in (0x1F, 0x20):  # check-cast / instance-of (22c)
                tidx = struct.unpack_from('<H', code, j * 2 + 2)[0]
                print(f'  pc={j:5d} {"instance-of" if op==0x20 else "check-cast "} type={get_type(tidx)}')
                j += 2; continue
            if op == 0x0A or op == 0x0B or op == 0x0C or op == 0x0D:
                j += 1; continue
            # crude length skip via opcode width table (common formats)
            w = 1
            if op in (0x12, 0x13, 0x1A, 0x1B, 0x22, 0x62, 0x6E, 0x6F, 0x70, 0x71, 0x72, 0x54, 0x59, 0x5A, 0x5B, 0x5C, 0x1C, 0x1D, 0x1E, 0x21, 0x23, 0x24, 0x25, 0x26, 0x74, 0x75, 0x76, 0x77, 0x78, 0x0E, 0x0F, 0x10, 0x11, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C):
                w = 1 if op in (0x12, 0x27, 0x28, 0x0E, 0x0F, 0x10, 0x11, 0x1D, 0x1E) else 2
                if op in (0x1B, 0x26, 0x77, 0x78): w = 3
            elif op in (0x00,):
                # nop / packed-switch payload — crude
                w = 1
                if j + 1 < insns_size:
                    ident = struct.unpack_from('<H', code, j * 2 + 2)[0] if False else 0
            elif op >= 0x2B:  # switches/sparse
                w = 3
            elif op in (0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1B):
                w = {0x14:2, 0x15:2, 0x16:1, 0x17:2, 0x18:3, 0x19:1, 0x1B:3}[op]
            elif op == 0x73 or op in range(0x73, 0x79):
                w = 2
            else:
                w = 1
            j += max(1, w)
if not found:
    print(f'{CLS} not found in class_defs')
