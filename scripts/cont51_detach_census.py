#!/usr/bin/env python3
"""cont51_detach_census.py — census every invoke of the ViewGroup detach/
attach family in solitaire classes.dex (which bridge surface the fix must
cover), using the single-class walker over the androidx+app classes only
(scoped: classes whose descriptor contains /v7/widget/ or /design/ or
de/tobiasbielefeld/)."""
import struct, zipfile, sys

src = open('scripts/cont46_disasm.py').read().split('def main')[0]
exec(src)

z = zipfile.ZipFile('upload/cont50_apks/de.tobiasbielefeld.solitaire_71.apk')
dx = Dex(z.read('classes.dex'))

FAMILY = {
    'detachViewFromParent', 'detachAllViewsFromParent', 'attachViewToParent',
    'removeDetachedView', 'detachViews', 'attachViews',
}

# collect method ids in the family
fam_ids = {}
for i in range(dx.mth_n):
    c, n, sig = dx.meth(i)
    if n in FAMILY:
        fam_ids.setdefault((c, n), i)

print(f'family method ids: {len(fam_ids)}')
for (c, n), i in sorted(fam_ids.items()):
    print(f'  {c}->{n} id={i}')

idset = set(fam_ids.values())

# scoped scan: androidx/design/app classes
hits = {}
diverged = 0
scanned = 0
for ci in range(dx.cdef_n):
    off = dx.cdef_off + ci * 32
    cls_idx = struct.unpack_from('<I', dx.b, off)[0]
    cls = dx.t(cls_idx)
    if not any(p in cls for p in ('/v7/widget/', '/design/', 'de/tobiasbielefeld/', '/v4/view/')):
        continue
    cd_off, _ = struct.unpack_from('<II', dx.b, off + 24)
    if cd_off == 0:
        continue
    try:
        p = cd_off
        sf, p = uleb(dx.b, p)
        inf, p = uleb(dx.b, p)
        dm, p = uleb(dx.b, p)
        vm, p = uleb(dx.b, p)
        for _ in range(sf + inf):
            _d, p = uleb(dx.b, p)
            _d, p = uleb(dx.b, p)
        midx = 0
        for cnt in (dm, vm):
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
                while q + 1 < end:
                    op = dx.b[q]
                    if op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
                        mid2 = struct.unpack_from('<H', dx.b, q + 2)[0]
                        if mid2 in idset:
                            tc, tn, tsig = dx.meth(mid2)
                            hits.setdefault((cls, n + sig), []).append(
                                f'->{tn}{tsig} @pc={q - insns_off}')
                    sz = 3 if op in (0x6e, 0x6f, 0x70, 0x71, 0x72) else 1
                    fmt = OPS.get(op, ('?', '10x'))[1]
                    sz = FMT_W.get(fmt, 1)
                    q += 2 * sz
                scanned += 1
    except (IndexError, struct.error):
        diverged += 1

print(f'scanned {scanned} methods ({diverged} diverged), {len(hits)} callers')
for (cls, m), calls in sorted(hits.items()):
    for c in calls:
        print(f'{cls} {m} {c}')
