#!/usr/bin/env python3
"""cont153_s0disasm.py — corrected-walker disassembly of Lpz0;.S0 (and its field reads).
The cls/disasm tools carry a direct+virtual cumulative-index bug; this walks
each list with its own restart, per the dex spec."""
import struct, zipfile

APK = 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
zf = zipfile.ZipFile(APK)
dex = zf.read('classes.dex')
str_size, str_off = struct.unpack_from('<2I', dex, 0x38)
type_size, type_off = struct.unpack_from('<2I', dex, 0x40)
field_size, field_off = struct.unpack_from('<2I', dex, 0x50)
meth_size, meth_off = struct.unpack_from('<2I', dex, 0x58)
class_size, class_off = struct.unpack_from('<2I', dex, 0x60)

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1; r |= (x & 0x7f) << s
        if not (x & 0x80): break
        s += 7
    return r, o

soa = struct.unpack_from(f'<{str_size}I', dex, str_off)
def str_at(si):
    off = soa[si]; _, o = uleb(dex, off)
    return dex[o:dex.index(b'\x00', o)].decode('utf-8', 'replace')

tds = [str_at(struct.unpack_from('<I', dex, type_off + t*4)[0]) for t in range(type_size)]
fids = [(tds[c], tds[t], str_at(n)) for c, t, n in
        (struct.unpack_from('<HHI', dex, field_off + i*8) for i in range(field_size))]
mnames = []
for k in range(meth_size):
    c, _, n = struct.unpack_from('<HHI', dex, meth_off + k*8)
    mnames.append((tds[c], str_at(n)))

# locate Lpz0;.S0 code_off
code_off = None; regn = None
for i in range(class_size):
    c = struct.unpack_from('<I', dex, class_off + i*32)[0]
    if tds[c] != 'Lpz0;': continue
    cdata = struct.unpack_from('<I', dex, class_off + i*32 + 24)[0]
    p = cdata
    sf, p = uleb(dex, p); inf, p = uleb(dex, p)
    dm, p = uleb(dex, p); vm, p = uleb(dex, p)
    for _ in range(sf): _, p = uleb(dex, p); _, p = uleb(dex, p)
    for _ in range(inf): _, p = uleb(dex, p); _, p = uleb(dex, p)
    for lst, cnt in (('direct', dm), ('virtual', vm)):
        midx = 0
        for _ in range(cnt):
            md, p = uleb(dex, p); _, p = uleb(dex, p); co, p = uleb(dex, p)
            midx += md
            if mnames[midx] == ('Lpz0;', 'S0') and co:
                code_off = co
                regn = struct.unpack_from('<H', dex, co)[0]
                print(f'FOUND Lpz0;.S0 ({lst}) code_off={co} registers={regn&0xff} ins={regn>>8}')
if code_off is None:
    print('S0 not found'); raise SystemExit(1)

insz = struct.unpack_from('<I', dex, code_off + 12)[0]
insns_off = code_off + 16
print(f'insns={insz}')

SIZES = [2]*256
for op in range(0x00, 0x08): SIZES[op] = 1
SIZES[0x0d]=1; SIZES[0x0e]=1; SIZES[0x0f]=1; SIZES[0x10]=1; SIZES[0x11]=1; SIZES[0x12]=1
SIZES[0x1d]=1; SIZES[0x1e]=1; SIZES[0x21]=1; SIZES[0x27]=1; SIZES[0x28]=1
for op in range(0x7b, 0x90): SIZES[op] = 1
for op in range(0xb0, 0xd0): SIZES[op] = 1
SIZES[0x13]=2; SIZES[0x15]=2; SIZES[0x16]=2; SIZES[0x19]=2
SIZES[0x14]=3; SIZES[0x18]=5
for op in range(0x38,0x3e): SIZES[op]=2
SIZES[0x1a]=2; SIZES[0x1c]=2; SIZES[0x1f]=2; SIZES[0x20]=2
SIZES[0x22]=2; SIZES[0x23]=2; SIZES[0x17]=3; SIZES[0x1b]=3
SIZES[0x24]=3; SIZES[0x25]=3; SIZES[0x26]=3
SIZES[0x29]=2; SIZES[0x2a]=3; SIZES[0x2b]=3; SIZES[0x2c]=3
for op in range(0x2d,0x32): SIZES[op]=2
for op in range(0x44,0x52): SIZES[op]=2
for op in range(0x52,0x5e): SIZES[op]=2
SIZES[0x5e]=2; SIZES[0x5f]=2
for op in range(0x60,0x6e): SIZES[op]=2
for op in range(0x6e,0x73): SIZES[op]=3
for op in range(0x74,0x79): SIZES[op]=3
for op in range(0x90,0xb0): SIZES[op]=2
for op in range(0xd0,0xe3): SIZES[op]=2
SIZES[0xfa]=4; SIZES[0xfb]=4
SIZES[0xfc]=3; SIZES[0xfd]=3; SIZES[0xfe]=3; SIZES[0xff]=3

pc = 0
while pc < insz:
    unit = struct.unpack_from('<H', dex, insns_off + pc*2)[0]
    if unit == 0x0100:
        pc += struct.unpack_from('<H', dex, insns_off + pc*2 + 2)[0]*2 + 4; continue
    if unit == 0x0200:
        pc += struct.unpack_from('<H', dex, insns_off + pc*2 + 2)[0]*4 + 2; continue
    op = unit & 0xff
    sz = max(1, SIZES[op])
    ref = struct.unpack_from('<H', dex, insns_off + pc*2 + 2)[0] if sz >= 2 else None
    note = ''
    if op in (0x54, 0x52, 0x53, 0x55, 0x56, 0x57, 0x58) and ref is not None:
        c, t, n = fids[ref]
        note = f'iget {c} {t} {n}'
    elif 0x59 <= op <= 0x5f and ref is not None:
        c, t, n = fids[ref]
        note = f'iput {c} {t} {n}'
    elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72) and ref is not None:
        c, n = mnames[ref]
        note = f'invoke {c}.{n}'
    elif op == 0x1a and ref is not None:
        note = f'const-string @{ref}'
    print(f'{pc:5d}: op{op:02x} unit={unit:#06x} {note}')
    pc += sz
