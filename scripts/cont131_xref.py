#!/usr/bin/env python3
"""CONT-131: dex xref scan — who calls Ln20;.addAll in dooz."""
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

def mid(idx):
    if idx >= m_size: return ('?', '?')
    ci, pi, ni = struct.unpack_from('<HHI', dex, m_off + idx * 8)
    return (tds[ci] if ci < len(tds) else '?', str_at(ni) if ni < str_size else f'OOB{ni}')

target = [i for i in range(m_size) if mid(i)[0] == 'Ln20;' and mid(i)[1] == 'addAll']
print('Ln20;.addAll method_idx:', target)
t = target[0]

found = []
for c in range(c_size):
    cd = struct.unpack_from('<8I', dex, c_off + c * 32)
    cls = tds[cd[0]]
    o = cd[6]
    if o == 0: continue
    sfs, o = uleb(dex, o); ifs, o = uleb(dex, o); dms, o = uleb(dex, o); vms, o = uleb(dex, o)
    for lst, cnt in (('DM', dms), ('VM', vms)):
        midx = 0  # list-local reset (CONT-130 law)
        for i in range(cnt):
            d, o = uleb(dex, o); a, o = uleb(dex, o); co, o = uleb(dex, o)
            midx += d
            if co == 0: continue
            regs, ins, outs, tries = struct.unpack_from('<4H', dex, co)
            dbg, insns = struct.unpack_from('<2I', dex, co + 8)
            if insns == 0 or co + 16 + insns * 2 > len(dex): continue
            body = dex[co + 16: co + 16 + insns * 2]
            for pc in range(0, len(body) - 3, 2):
                op = body[pc]
                if 0x6e <= op <= 0x72:
                    mref = struct.unpack_from('<H', body, pc + 2)[0]
                    if mref == t:
                        nm = mid(midx)[1]
                        found.append(f'{cls}.{nm} ({lst}[{i}] op={op:#x} pc={pc})')
print('callers of Ln20;.addAll:')
for f in found[:12]: print('  ', f)
print('total:', len(found))
