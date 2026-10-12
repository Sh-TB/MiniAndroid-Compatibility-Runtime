#!/usr/bin/env python3
"""cont51_dbg_scan.py — focused iput scanner debug: walk ONE class's methods
using the helper's methods_of, count iput-family instructions and any hits
on a target field id."""
import struct, zipfile, sys

src = open('scripts/cont46_disasm.py').read().split('def main')[0]
exec(src)

z = zipfile.ZipFile('upload/cont50_apks/de.tobiasbielefeld.solitaire_71.apk')
dx = Dex(z.read('classes.dex'))

cls = sys.argv[1]
fld = sys.argv[2]  # e.g. 'ay$i;.c' -> class 'Landroid/support/v7/widget/ay$i;', name 'c'
cls_part, fld_name = fld.split(';.')
target_cls = 'Landroid/support/v7/widget/' + cls_part + ';'

target_fidx = set()
for i in range(dx.fld_n):
    c, n, t = dx.field(i)
    if c == target_cls and n == fld_name:
        target_fidx.add(i)
print(f'target field ids: {target_fidx}')

hdr = dx.find_class(cls)
iput_count = 0
hits = 0
for kind, midx, acc, code_off in dx.methods_of(hdr):
    if not code_off: continue
    c, n, sig = dx.meth(midx)
    regs, ins, outs, insns_off, insns_n = dx.code(code_off)
    q = insns_off
    end = insns_off + insns_n * 2
    pc = 0
    while q + 1 < end:
        op = dx.b[q]
        if op in (0x59, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f):
            iput_count += 1
            fidx2 = struct.unpack_from('<H', dx.b, q + 2)[0]
            if fidx2 in target_fidx:
                hits += 1
                print(f'  HIT {n}{sig} pc={pc} op=0x{op:02x}')
        if op in (0x2b, 0x2c):
            tgt = struct.unpack_from('<i', dx.b, q + 2)[0]
            ident = struct.unpack_from('<H', dx.b, tgt * 2)[0]
            psz = struct.unpack_from('<I', dx.b, tgt * 2 + 4)[0]
            sz = (tgt + 2 + (psz * 2 if ident == 0x0100 else psz * 4)) - pc
            pc += max(sz, 1)
            q += 2 * max(sz, 1)
            continue
        fmt = OPS.get(op, ('?', '10x'))[1]
        sz = FMT_W.get(fmt, 1)
        pc += sz
        q += 2 * sz
print(f'class {cls}: {iput_count} iput-family insns, {hits} hits on {fld}')
