#!/usr/bin/env python3
"""CONT-136 Train 1: Ljt1; (AndroidCanvas bridge) static truth in dooz.
- class_def + method table
- ALL invoke sites to ANY Ljt1; method (with enclosing class;method)
- guard branch analysis: which methods would construct it (new-instance Ljt1;)
"""
import struct, zipfile

z = zipfile.ZipFile('upload/canonical_apks/io.github.yamin8000.dooz_23.apk')
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
m_size, m_off = struct.unpack_from('<2I', dex, 0x58)
c_size, c_off = struct.unpack_from('<2I', dex, 0x60)
soa = struct.unpack_from(f'<{str_size}I', dex, str_off)

def str_at(si):
    off = soa[si]; _, o = uleb(dex, off)
    return dex[o:dex.index(b"\x00", o)].decode('utf-8', 'replace')

tds = [str_at(struct.unpack_from('<I', dex, type_off + t * 4)[0]) for t in range(type_size)]
mids = []
for i in range(m_size):
    ci, pi, ni = struct.unpack_from('<HHI', dex, m_off + i * 8)
    mids.append((tds[ci], str_at(ni)))

found = False
for c in range(c_size):
    cd = struct.unpack_from('<8I', dex, c_off + c * 32)
    if tds[cd[0]] == 'Ljt1;':
        found = True
        sup = tds[cd[1]] if cd[1] < type_size else '?'
        print('Ljt1; FOUND superclass:', sup)
        o = cd[6]
        if o:
            sfs, o = uleb(dex, o); ifs, o = uleb(dex, o); dms, o = uleb(dex, o); vms, o = uleb(dex, o)
            print('hdr', sfs, ifs, dms, vms)
            for _ in range(sfs + ifs):
                _, o = uleb(dex, o); _, o = uleb(dex, o)
            for lst, cnt in (('DM', dms), ('VM', vms)):
                midx = 0
                for i in range(cnt):
                    d, o = uleb(dex, o); a, o = uleb(dex, o); co, o = uleb(dex, o)
                    midx += d
                    if midx < m_size:
                        print(' ', lst, mids[midx], 'code@', co)
        break
if not found:
    print('Ljt1; NOT in dex')

INVOKE = set(range(0x6e, 0x73)) | set(range(0x74, 0x79))
NEWINS = 0x22
tgt = {i for i, m in enumerate(mids) if m[0] == 'Ljt1;'}
print('Ljt1; method_ids:', len(tgt))
callers = {}
newers = {}
for c in range(c_size):
    cd = struct.unpack_from('<8I', dex, c_off + c * 32)
    cls = tds[cd[0]]
    o = cd[6]
    if o == 0: continue
    sfs, o = uleb(dex, o); ifs, o = uleb(dex, o); dms, o = uleb(dex, o); vms, o = uleb(dex, o)
    for _ in range(sfs + ifs):
        _, o = uleb(dex, o); _, o = uleb(dex, o)
    for lst, cnt in (('DM', dms), ('VM', vms)):
        midx = 0
        for i in range(cnt):
            d, o = uleb(dex, o); a, o = uleb(dex, o); co, o = uleb(dex, o)
            midx += d
            if co == 0 or co + 16 > len(dex) or midx >= m_size: continue
            mn = mids[midx][1]
            regs, ins, outs, tries = struct.unpack_from('<4H', dex, co)
            dbg, insns = struct.unpack_from('<2I', dex, co + 8)
            if insns == 0 or co + 16 + insns * 2 > len(dex): continue
            body = dex[co + 16: co + 16 + insns * 2]
            pc = 0
            while pc + 2 < len(body):
                op = body[pc]
                sz = 2
                if op in (0x6e, 0x6f, 0x70, 0x71, 0x72) and pc + 4 < len(body):
                    mr = struct.unpack_from('<H', body, pc + 2)[0]; sz = 3
                    if mr < m_size and mr in tgt:
                        callers.setdefault(mids[mr][1], set()).add(f'{cls};.{mn}')
                elif op in (0x74, 0x76, 0x77, 0x78) and pc + 5 < len(body):
                    mr = struct.unpack_from('<H', body, pc + 4)[0]; sz = 4
                    if mr < m_size and mr in tgt:
                        callers.setdefault(mids[mr][1], set()).add(f'{cls};.{mn}')
                elif op == 0x22 and pc + 3 < len(body):
                    tr = struct.unpack_from('<H', body, pc + 2)[0]
                    if tr < type_size and tds[tr] == 'Ljt1;':
                        newers.setdefault(mn, set()).add(cls)
                elif op in (0x00, 0x12, 0x0e, 0x0f, 0x10, 0x11, 0x27, 0x1d, 0x1e, 0x28):
                    sz = 1
                pc += sz

for k, v in sorted(callers.items()):
    print('invoke sites of Ljt1;.' + k, sorted(v)[:8])
for k, v in sorted(newers.items()):
    print('new-instance Ljt1; in', k, sorted(v)[:8])
if not callers and not newers:
    print('NO static references to Ljt1; methods or construction anywhere in dex')
