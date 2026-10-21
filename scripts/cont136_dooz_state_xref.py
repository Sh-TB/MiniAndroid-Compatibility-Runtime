#!/usr/bin/env python3
"""CONT-136 Train 1: dooz state-map publish-path xref.
Targets:
  A) field Ld61;->i  — all iget/iput/sget/sput sites + its descriptor
  B) static field Ln20;->e (kotlin EmptyMap INSTANCE) — all sget/sput sites
  C) Ld61; method table (name+proto) to identify the publisher
  D) callers of each Ld61; method (invoke sites)
CONT-130 law: method-id deltas reset per encoded-list.
"""
import struct, zipfile, json, sys

APK = 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
z = zipfile.ZipFile(APK)
dex = z.read('classes.dex')

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

str_size, str_off = struct.unpack_from('<2I', dex, 0x38)
type_size, type_off = struct.unpack_from('<2I', dex, 0x40)
p_size, p_off = struct.unpack_from('<2I', dex, 0x48)   # proto_ids
f_size, f_off = struct.unpack_from('<2I', dex, 0x50)   # field_ids
m_size, m_off = struct.unpack_from('<2I', dex, 0x58)   # method_ids
c_size, c_off = struct.unpack_from('<2I', dex, 0x60)   # class_defs
soa = struct.unpack_from(f'<{str_size}I', dex, str_off)

def str_at(si):
    off = soa[si]; _, o = uleb(dex, off)
    return dex[o:dex.index(b"\x00", o)].decode('utf-8', 'replace')

tds = [str_at(struct.unpack_from('<I', dex, type_off + t * 4)[0]) for t in range(type_size)]

def proto_at(pi):
    si, ri, pi2 = struct.unpack_from('<3I', dex, p_off + pi * 12)
    ret = str_at(ri)
    _, o = uleb(dex, pi2)
    n, o = uleb(dex, o)
    ps = []
    for _ in range(n):
        ti, o = uleb(dex, o)
        ps.append(tds[ti] if ti < len(tds) else '?')
    return '(' + ' '.join(ps) + ')' + ret

fids = []
for i in range(f_size):
    ci, ti, ni = struct.unpack_from('<HHI', dex, f_off + i * 8)
    fids.append((tds[ci] if ci < len(tds) else '?', tds[ti] if ti < len(tds) else '?', str_at(ni) if ni < str_size else '?'))

mids = []
for i in range(m_size):
    ci, pi, ni = struct.unpack_from('<HHI', dex, m_off + i * 8)
    mids.append((tds[ci] if ci < len(tds) else '?', proto_at(pi) if pi < p_size else '?', str_at(ni) if ni < str_size else '?'))

# ---- collect all field-op and invoke-op sites across all classes
IGET = set(range(0x52, 0x59)); IPUT = set(range(0x59, 0x60))
SGET = set(range(0x60, 0x67)); SPUT = set(range(0x68, 0x6E))
INVOKE = set(range(0x6E, 0x73)) | set(range(0x74, 0x79))

class_code = {}   # cls -> list of (mname, mproto, code_off)
field_sites = []  # (kind, fidx, cls, mname, pc)
call_sites = []   # (midx, cls, mname, pc)

for c in range(c_size):
    cd = struct.unpack_from('<8I', dex, c_off + c * 32)
    cls = tds[cd[0]]
    o = cd[6]
    if o == 0: continue
    sfs, o = uleb(dex, o); ifs, o = uleb(dex, o); dms, o = uleb(dex, o); vms, o = uleb(dex, o)
    # encoded_field lists MUST be consumed before method deltas (fix: earlier scan corrupted names/code-offs)
    fidx = 0
    for _ in range(sfs):
        d, o = uleb(dex, o); a, o = uleb(dex, o); fidx += d
    fidx = 0
    for _ in range(ifs):
        d, o = uleb(dex, o); a, o = uleb(dex, o); fidx += d
    methods = []
    for lst, cnt in (('DM', dms), ('VM', vms)):
        midx = 0
        for i in range(cnt):
            d, o = uleb(dex, o); a, o = uleb(dex, o); co, o = uleb(dex, o)
            midx += d
            methods.append((midx, co))
    for midx, co in methods:
        if co == 0: continue
        mi = mids[midx] if midx < m_size else ('?', '?', '?')
        class_code.setdefault(cls, []).append((mi[2], mi[1], co))
        if co + 16 > len(dex): continue
        regs, ins, outs, tries = struct.unpack_from('<4H', dex, co)
        dbg, insns = struct.unpack_from('<2I', dex, co + 8)
        if insns == 0 or co + 16 + insns * 2 > len(dex): continue
        body = dex[co + 16: co + 16 + insns * 2]
        for pc in range(0, len(body) - 3, 2):
            op = body[pc]
            if op in IGET or op in IPUT or op in SGET or op in SPUT:
                fref = struct.unpack_from('<H', body, pc + 2)[0]
                kind = 'iget' if op in IGET else 'iput' if op in IPUT else 'sget' if op in SGET else 'sput'
                field_sites.append((kind, fref, cls, mi[2], pc))
            elif op in INVOKE:
                mref = struct.unpack_from('<H', body, pc + 2)[0]
                call_sites.append((mref, cls, mi[2], pc))

print('class_defs:', c_size, 'field sites:', len(field_sites), 'call sites:', len(call_sites))

# A) Ld61;->i
fi = [i for i, (cl, ty, nm) in enumerate(fids) if cl == 'Ld61;' and nm == 'i']
print('\n== A) Ld61;->i field_ids:', [(i, fids[i]) for i in fi])
for i in fi:
    sites = [s for s in field_sites if s[1] == i]
    for kind in ('iget', 'iput', 'sget', 'sput'):
        ss = [s for s in sites if s[0] == kind]
        if ss:
            fromc = sorted(set(s[2] for s in ss))
            print(f'  {kind}: {len(ss)} sites from classes {fromc[:8]}')
            for s in ss[:20]:
                print(f'    {s[2]};.{s[3]} @pc{s[4]}')

# methods of Ld61;
print('\n== C) Ld61; methods:')
for nm, pr, co in class_code.get('Ld61;', []):
    print(f'  {nm} {pr} code@{co}')

# D) callers of Ld61; methods
ld61_idx = {i for i, m in enumerate(mids) if m[0] == 'Ld61;'}
callers = {}
for mref, cls, mname, pc in call_sites:
    if mref in ld61_idx:
        tgt = mids[mref]
        callers.setdefault(f"{tgt[2]}{tgt[1]}", []).append(f"{cls};.{mname}")
print('\n== D) callers of Ld61; methods:')
for k, v in sorted(callers.items()):
    uc = sorted(set(x.rsplit('.', 1)[0] if False else x for x in v))
    print(f'  {k} <- {len(v)} sites from {sorted(set(v))[:6]}')

# B) Ln20;->e
fe = [i for i, (cl, ty, nm) in enumerate(fids) if cl == 'Ln20;' and nm == 'e']
print('\n== B) Ln20;->e field_ids:', [(i, fids[i]) for i in fe])
for i in fe:
    sites = [s for s in field_sites if s[1] == i]
    g = [s for s in sites if s[0] == 'sget']; p = [s for s in sites if s[0] == 'sput']
    print(f'  sget: {len(g)} | sput: {len(p)}')
    from collections import Counter
    cc = Counter((s[2], s[3]) for s in g)
    for (c2, m2), n in cc.most_common(12):
        print(f'    sget {c2};.{m2} x{n}')
