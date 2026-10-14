#!/usr/bin/env python3
"""cont51_flags_scan.py — census every iput on ay$w.n (ViewHolder.mFlags)
in solitaire classes.dex, with the const that feeds it (nearest
const/const/16 within 6 units before), plus every and-int/lit8 mask
literal used against it (the r()/c()/shouldIgnore family)."""
import struct, zipfile, sys

src = open('scripts/cont46_disasm.py').read().split('def main')[0]
exec(src)

z = zipfile.ZipFile('upload/cont50_apks/de.tobiasbielefeld.solitaire_71.apk')
dx = Dex(z.read('classes.dex'))

# find field id for ay$w.n
target_fidx = None
for i in range(dx.fld_n):
    c, n, t = dx.field(i)
    if c == 'Landroid/support/v7/widget/ay$w;' and n == 'n':
        target_fidx = i
        print('ay$w.n field idx', i, 'type', t)

hits = []
diverged = 0
total_iput = 0
for ci in range(dx.cdef_n):
    off = dx.cdef_off + ci * 32
    cls_idx = struct.unpack_from('<I', dx.b, off)[0]
    cls = dx.t(cls_idx)
    cd_off, cd_n = struct.unpack_from('<II', dx.b, off + 24)
    if cd_off == 0:
        continue
    try:
        p = cd_off
        sf, p = uleb(dx.b, p)
        inf, p = uleb(dx.b, p)
        dm, p = uleb(dx.b, p)
        vm, p = uleb(dx.b, p)
        fidx = 0
        for _ in range(sf + inf):
            d, p = uleb(dx.b, p); fidx += d
            d, p = uleb(dx.b, p)
        midx = 0
        for kind_n, cnt in (('direct', dm), ('virtual', vm)):
            for _ in range(cnt):
                d, p = uleb(dx.b, p); midx += d
                acc, p = uleb(dx.b, p)
                code_off, p = uleb(dx.b, p)
                if not code_off:
                    continue
                c, n, sig = dx.meth(midx)
                regs, ins, outs, insns_off, insns_n = dx.code(code_off)
                q = insns_off
                end = insns_off + insns_n * 2
                pc = 0
                last_const = None
                while q + 1 < end:
                    op = dx.b[q]
                    if op in (0x12,):
                        lit = (dx.b[q + 1] >> 4) & 0xf
                        if lit >= 8: lit -= 16
                        last_const = lit
                    elif op in (0x13,):
                        last_const = struct.unpack_from('<h', dx.b, q + 2)[0]
                    elif op in (0x14,):
                        last_const = struct.unpack_from('<i', dx.b, q + 2)[0]
                    elif op in (0x59, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f):
                        total_iput += 1
                        fidx2 = struct.unpack_from('<H', dx.b, q + 2)[0]
                        if fidx2 == target_fidx:
                            hits.append((cls, n, sig, pc, op, last_const))
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
    except (IndexError, struct.error):
        diverged += 1
        continue

print(f'== {len(hits)} iput sites on ay$w.n ({total_iput} total iput scanned, {diverged} diverged classes skipped) ==')
for cls, n, sig, pc, op, lc in hits:
    print(f'{cls}->{n}{sig} pc={pc} op=0x{op:02x} last_const={lc}')
