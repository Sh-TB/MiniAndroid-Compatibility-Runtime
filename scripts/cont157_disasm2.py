#!/usr/bin/env python3
"""cont157_disasm2.py — dooz white-screen decode, clean rewrite.
Usage: cont157_disasm2.py <class-desc> <method> [method2 ...]"""
import struct, zipfile, sys

APK = 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
zf = zipfile.ZipFile(APK)
dex_data = zf.read('classes.dex')

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

d = dex_data
str_size, str_off = struct.unpack_from('<2I', d, 0x38)
type_size, type_off = struct.unpack_from('<2I', d, 0x40)
proto_size, proto_off = struct.unpack_from('<2I', d, 0x48)
field_size, field_off = struct.unpack_from('<2I', d, 0x50)
meth_size, meth_off = struct.unpack_from('<2I', d, 0x58)
class_size, class_off = struct.unpack_from('<2I', d, 0x60)
soa = struct.unpack_from(f'<{str_size}I', d, str_off)

def str_at(si):
    off = soa[si]; _, o = uleb(d, off)
    return d[o:d.index(b'\x00', o)].decode('utf-8', 'replace')

tds = [str_at(struct.unpack_from('<I', d, type_off + t*4)[0]) for t in range(type_size)]
fids = [(tds[c], tds[t], str_at(n)) for c, t, n in
        (struct.unpack_from('<HHI', d, field_off + i*8) for i in range(field_size))]
mids = [(tds[c], str_at(n), p) for c, p, n in
        (struct.unpack_from('<HHI', d, meth_off + i*8) for i in range(meth_size))]

def proto_str(pi):
    ret_idx = struct.unpack_from('<I', d, proto_off + pi*12 + 4)[0]
    poff = struct.unpack_from('<I', d, proto_off + pi*12 + 8)[0]
    ret = tds[ret_idx]
    params = ''
    if poff:
        cnt = struct.unpack_from('<I', d, poff)[0]
        plist = struct.unpack_from(f'<{cnt}H', d, poff+4)
        params = ''.join(tds[p] for p in plist)
    return params, ret

classes = {}
for i in range(class_size):
    cidx, acc, sup, ifo, src, ann, cd_off, stv = struct.unpack_from('<8I', d, class_off + i*32)
    classes[tds[cidx]] = cd_off

SIZES = [2]*256
for op in range(0x00, 0x08): SIZES[op] = 1
SIZES[0x0f]=1; SIZES[0x10]=1; SIZES[0x11]=1; SIZES[0x12]=1
SIZES[0x08]=2; SIZES[0x09]=2; SIZES[0x0a]=1; SIZES[0x0e]=1
SIZES[0x0b]=1; SIZES[0x0c]=1; SIZES[0x0d]=1
SIZES[0x1d]=1; SIZES[0x1e]=1; SIZES[0x21]=1; SIZES[0x27]=1; SIZES[0x28]=1
for op in range(0x7b, 0x90): SIZES[op] = 1
for op in range(0xb0, 0xd0): SIZES[op] = 1
SIZES[0x13]=2; SIZES[0x15]=2; SIZES[0x16]=2; SIZES[0x19]=2
SIZES[0x14]=3; SIZES[0x18]=5
for op in range(0x38,0x3e): SIZES[op]=2
SIZES[0x1a]=2; SIZES[0x1c]=2; SIZES[0x1f]=2; SIZES[0x20]=2
SIZES[0x22]=2; SIZES[0x23]=2
SIZES[0x17]=3; SIZES[0x1b]=3
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

def s16(v): return v - 0x10000 if v & 0x8000 else v
def s32(v): return v - 0x100000000 if v & 0x80000000 else v

def disasm(insns):
    out = []
    i = 0; n = len(insns)
    while i < n:
        start = i
        w = insns[i]; op = w & 0xff
        if w == 0x0100:
            sz = insns[i+1] if i+1 < n else 0
            out.append((start, f'packed-switch-payload({sz})')); i += 4 + sz*2; continue
        if w == 0x0200:
            sz = insns[i+1] if i+1 < n else 0
            out.append((start, f'sparse-switch-payload({sz})')); i += 2 + sz*4; continue
        if w == 0x0300:
            ew = insns[i+1] if i+1 < n else 0
            sz = (insns[i+2] | (insns[i+3] << 16)) if i+3 < n else 0
            out.append((start, f'fill-array-data-payload(w={ew},n={sz})'))
            i += 4 + (sz*ew + 1)//2; continue
        size = SIZES[op]
        nxt = lambda k: insns[i+k] if i+k < n else 0
        try:
            if op == 0x12:
                out.append((start, f'const/4 v{w>>12&0xf}, {((w>>8&0xf)^8)-8}'))
            elif op in (0x01,0x04,0x07):
                out.append((start, f'op{op:#04x} v{w>>8&0xf}, v{w>>12&0xf}'))
            elif op in (0x02,0x05,0x08):
                out.append((start, f'op{op:#04x} v{w>>8&0xff}, v{nxt(1)}'))
            elif op in (0x0a,0x0b,0x0c,0x0d,0x0f,0x10,0x11,0x1d,0x1e,0x21,0x27):
                out.append((start, f'op{op:#04x} v{w>>8&0xff}'))
            elif op in (0x13,0x16):
                out.append((start, f'op{op:#04x} v{w>>8&0xff}, {s16(nxt(1))}'))
            elif op in (0x14,0x17):
                out.append((start, f'op{op:#04x} v{w>>8&0xff}, {s32(nxt(1)|nxt(2)<<16)}'))
            elif op == 0x1a:
                out.append((start, f'const-string v{w>>8&0xff}, "{str_at(nxt(1))[:70]}"'))
            elif op in (0x1c,0x1f,0x20,0x22,0x23):
                out.append((start, f'op{op:#04x} v{w>>8&0xff}, {tds[nxt(1)]}'))
            elif op == 0x28:
                out.append((start, f'goto {(((w>>8&0xff)^0x80)-0x80):+d}'))
            elif op == 0x29:
                out.append((start, f'goto/16 {s16(nxt(1)):+d}'))
            elif 0x32 <= op <= 0x37:
                out.append((start, f'if-cmp v{w>>8&0xf}, v{w>>12&0xf}, {s16(nxt(1)):+d}'))
            elif 0x38 <= op <= 0x3d:
                out.append((start, f'if-z v{w>>8&0xff}, {s16(nxt(1)):+d}'))
            elif 0x44 <= op <= 0x51:
                out.append((start, f'arr-op{op:#04x} v{w>>8&0xff}, v{w>>12&0xf}'))
            elif 0x52 <= op <= 0x6d:
                fc, ft, fn = fids[nxt(1)]
                if op < 0x59:
                    out.append((start, f'iop{op:#04x} v{w>>8&0xf}, v{w>>12&0xf}  {fc}->{fn}:{ft}'))
                else:
                    out.append((start, f'sop{op:#04x} v{w>>8&0xff}  {fc}->{fn}:{ft}'))
            elif 0x6e <= op <= 0x78:
                bc = nxt(1); mi = bc & 0xffff
                mc, mn, mp = mids[mi]
                params, ret = proto_str(mp)
                kind = {0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
                        0x71:'invoke-static',0x72:'invoke-interface'}.get(op, f'invoke-x{op:#04x}/range')
                if op < 0x74:
                    v = w >> 8
                    regs = ','.join(f'v{(v>>(4*k))&0xf}' for k in range(4))
                    out.append((start, f'{kind} {{{regs}}}, {mc}->{mn}({params}){ret}'))
                else:
                    out.append((start, f'{kind} {{v{w>>8&0xff}..}}, {mc}->{mn}({params}){ret}'))
            elif 0x90 <= op <= 0xaf:
                out.append((start, f'binop{op:#04x} v{w>>8&0xff}, v{w>>12&0xf}, v{nxt(1)>>8&0xff}, v{nxt(1)&0xff}'))
            elif 0xb0 <= op <= 0xcf:
                out.append((start, f'bin2{op:#04x} v{w>>8&0xf}, v{w>>12&0xf}'))
            elif 0xd0 <= op <= 0xd7:
                out.append((start, f'lit16{op:#04x} v{w>>8&0xf}, v{w>>12&0xf}, {s16(nxt(1))}'))
            elif 0xd8 <= op <= 0xe2:
                out.append((start, f'lit8{op:#04x} v{w>>8&0xff}, v{w>>12&0xf}, {(nxt(1)^0x80)-0x80}'))
            else:
                out.append((start, f'op{op:#04x}'))
        except Exception as e:
            out.append((start, f'<err {e}>'))
        i += size
    return out

def dump(desc, meths):
    cd_off = classes.get(desc)
    print(f'==== class {desc}: {"OK" if cd_off else "ABSENT"}')
    if not cd_off: return
    o = cd_off
    sf, inf, dm, vm = uleb(d, o)[0], None, None, None
    sf, o = uleb(d, o)
    inf, o = uleb(d, o)
    dm, o = uleb(d, o)
    vm, o = uleb(d, o)
    idx = 0
    for _ in range(inf):
        diff, o = uleb(d, o); acc, o = uleb(d, o); idx += diff
        print(f'  ifield: {fids[idx][2]} : {fids[idx][1]}')
    idx = 0
    for _ in range(sf):
        diff, o = uleb(d, o); acc, o = uleb(d, o); idx += diff
        print(f'  sfield: {fids[idx][2]} : {fids[idx][1]}')
    for kind, cnt in (('direct', dm), ('virtual', vm)):
        idx = 0
        for _ in range(cnt):
            diff, o = uleb(d, o); acc, o = uleb(d, o); code_off, o = uleb(d, o); idx += diff
            mc, mn, mp = mids[idx]
            if meths and mn not in meths: continue
            params, ret = proto_str(mp)
            print(f'\n  [{kind}] {mn}({params}){ret}  code={code_off:#x}')
            if not code_off: continue
            reg, insz, outs, tries = struct.unpack_from('<4H', d, code_off)
            insns_sz = struct.unpack_from('<I', d, code_off + 12)[0]
            insns = struct.unpack_from(f'<{insns_sz}H', d, code_off + 16)
            for pc, txt in disasm(insns):
                print(f'    {pc:5d}: {txt}')

if __name__ == '__main__':
    desc = sys.argv[1]
    meths = set(sys.argv[2:]) or None
    dump(desc, meths)
