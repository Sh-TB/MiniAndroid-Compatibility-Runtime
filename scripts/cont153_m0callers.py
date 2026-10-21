#!/usr/bin/env python3
"""cont153_t0callers.py — invoke sites of ANY method_id named 'T0' (any ref-class,
superhierarchy law) + sput/iput sites of Lpz0;/Lwt0; int fields h/g (kind-flag writers)."""
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
mids = [(tds[c], str_at(n)) for c, _, n in
        (struct.unpack_from('<HHI', dex, meth_off + i*8) for i in range(meth_size))]

t0_mids = {i: mids[i] for i in range(meth_size) if mids[i][1] in ('M0', 'h1', 'T0')}
hg_fids = {i: fids[i] for i in range(field_size)
           if fids[i][2] in ('h', 'g') and fids[i][0] in ('Lpz0;', 'Lwt0;') and fids[i][1] == 'I'}
print(f'M0/h1/T0 method_ids: {[f"{c}.{n} @mid{i}" for i, (c, n) in t0_mids.items()]}')
print(f'h/g int fids: {[f"{c}.{n} @fid{i}" for i, (c, t, n) in hg_fids.items()]}')

SIZES = [2]*256
for op in range(0x00, 0x13): SIZES[op] = 1
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

def parse_methods(off, cnt):
    out = []; midx = 0; p = off
    for _ in range(cnt):
        mdiff, p = uleb(dex, p)
        acc, p = uleb(dex, p)
        code_off, p = uleb(dex, p)
        midx += mdiff
        if code_off: out.append((midx, code_off))
    return out

t0_sites = []; hg_writes = []
nclasses = 0
for i in range(class_size):
    c = struct.unpack_from('<I', dex, class_off + i*32)[0]
    cdata = struct.unpack_from('<I', dex, class_off + i*32 + 24)[0]
    if not cdata: continue
    nclasses += 1
    p = cdata
    sf, p = uleb(dex, p); inf, p = uleb(dex, p)
    dm, p = uleb(dex, p); vm, p = uleb(dex, p)
    for _ in range(sf):
        _, p = uleb(dex, p); _, p = uleb(dex, p)
    for _ in range(inf):
        _, p = uleb(dex, p); _, p = uleb(dex, p)
    ml = parse_methods(p, dm) + parse_methods(*reversed([*parse_methods(p, 0)]) ) if False else parse_methods(p, dm)
    # direct+virtual in sequence: parse dm then continue from returned pos
    p2 = p
    for _ in range(dm):
        _, p2 = uleb(dex, p2); _, p2 = uleb(dex, p2); _, p2 = uleb(dex, p2)
    ml = parse_methods(p, dm) + parse_methods(p2, vm)
    owner = tds[c]
    for midx, code_off in ml:
        insz = struct.unpack_from('<I', dex, code_off + 12)[0]
        insns_off = code_off + 16
        pc = 0
        while pc < insz:
            unit = struct.unpack_from('<H', dex, insns_off + pc*2)[0]
            if unit == 0x0100:
                pc += struct.unpack_from('<H', dex, insns_off + pc*2 + 2)[0]*2 + 4; continue
            if unit == 0x0200:
                pc += struct.unpack_from('<H', dex, insns_off + pc*2 + 2)[0]*4 + 2; continue
            if unit == 0x0300:
                ew = struct.unpack_from('<H', dex, insns_off + pc*2 + 2)[0]
                szn = struct.unpack_from('<H', dex, insns_off + pc*2 + 4)[0]
                pc += (szn*ew + 1)//2 + 4; continue
            op = unit & 0xff
            sz = max(1, SIZES[op])
            ref = struct.unpack_from('<H', dex, insns_off + pc*2 + 2)[0] if sz >= 2 else None
            if op in range(0x6e, 0x79) and ref in t0_mids:
                t0_sites.append((owner, mids[midx][1], f'{t0_mids[ref][0]}.T0', pc, hex(op)))
            if 0x59 <= op <= 0x5f and ref in hg_fids:  # iput family
                hg_writes.append((owner, mids[midx][1], f'iput {hg_fids[ref][0]}.{hg_fids[ref][2]}', pc))
            pc += sz

print(f'\nclasses with code: {nclasses}')
print(f'T0 invoke sites ({len(t0_sites)}):')
for s in t0_sites[:20]:
    print('  %s.%s -> %s pc=%d op=%s' % s)
print(f'h/g iput sites ({len(hg_writes)}):')
for s in hg_writes[:20]:
    print('  %s.%s %s pc=%d' % s)
