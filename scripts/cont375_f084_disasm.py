#!/usr/bin/env python3
"""cont375_f084_disasm.py — disassemble Lw4;.<init> from fairymahjong.
Focus: the F-NEW-084 halt loop at pc 0x7b..0xb2."""
import zipfile, struct, io

APK = '/home/z/my-project/apk_cache/com.fairytrick.fairymahjong_5.apk'
WANT_CLASS = 'Lw4;'
WANT_METHOD = '<init>'

z = zipfile.ZipFile(APK)
d = z.read('classes.dex')

ssz, sof = struct.unpack_from('<II', d, 0x38)
tsz, tof = struct.unpack_from('<II', d, 0x40)
psz, pof = struct.unpack_from('<II', d, 0x48)
fsz, fof = struct.unpack_from('<II', d, 0x50)
msz, mof = struct.unpack_from('<II', d, 0x58)
cds, cdo = struct.unpack_from('<II', d, 0x60)

def uleb(f):
    r = 0; s = 0
    while True:
        b = f.read(1)[0]; r |= (b & 0x7f) << s; s += 7
        if not b & 0x80: break
    return r

def string(idx):
    off = struct.unpack_from('<I', d, sof + idx*4)[0]
    f = io.BytesIO(d); f.seek(off)
    n = uleb(f)
    return f.read(n).decode('utf-8', 'replace')

def typeid(idx):
    si = struct.unpack_from('<I', d, tof + idx*4)[0]
    return string(si)

def fieldid(idx):
    cls, typ, name = struct.unpack_from('<HHI', d, fof + idx*8)
    return typeid(cls), typeid(typ), string(name)

def methodid(idx):
    cls, proto, name = struct.unpack_from('<HHI', d, mof + idx*8)
    return typeid(cls), string(name), string(struct.unpack_from('<I', d, pof + proto*12)[0])

class_data_off = None
for i in range(cds):
    off = cdo + i*32
    cidx = struct.unpack_from('<I', d, off)[0]
    if typeid(cidx) == WANT_CLASS:
        class_data_off = struct.unpack_from('<I', d, off + 24)[0]
        break
assert class_data_off, f'{WANT_CLASS} not found'

f = io.BytesIO(d); f.seek(class_data_off)
sf = uleb(f); inf_ = uleb(f); dm = uleb(f); vm = uleb(f)

def skip_fields(f, n):
    idx = 0
    for _ in range(n):
        idx += uleb(f); uleb(f)
    return idx

def read_methods(f, n):
    idx = 0; out = []
    for _ in range(n):
        idx += uleb(f); acc = uleb(f); co = uleb(f)
        out.append((idx, acc, co))
    return out

skip_fields(f, sf); skip_fields(f, inf_)
direct = read_methods(f, dm)
virtual = read_methods(f, vm)

for idx, acc, co in direct + virtual:
    cls, name, proto = methodid(idx)
    if name != WANT_METHOD: continue
    print(f'== {cls}.{name}{proto} access={acc:#x} code_off={co:#x}')
    reg, ins, outs, tries, dbg, insns = struct.unpack_from('<HHHHII', d, co)
    base = co + 16
    raw = d[base:base + insns*2]
    print(f'registers={reg} ins={ins} insns={insns}')
    # focus: pc 0x70..0xc0 with full decode
    i = 0
    while i < insns:
        unit = struct.unpack_from('<H', raw, i*2)[0]
        op = raw[i*2 + 1]
        if 0x70 <= i*2 <= 0xc8 or i in range(0x38, 0x64):
            extra = ''
            if op == 0x1a:
                bidx = struct.unpack_from('<H', raw, i*2+2)[0]
                extra = f'const-string "{string(bidx)[:60]}"'
            elif op in (0x62, 0x60, 0x63, 0x59, 0x5a, 0x54, 0x55):
                fidx = struct.unpack_from('<H', raw, i*2+2)[0]
                c2, t2, n2 = fieldid(fidx)
                extra = f'{c2}.{n2}:{t2}'
            elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
                midx = struct.unpack_from('<H', raw, i*2+2)[0]
                c2, n2, p2 = methodid(midx)
                extra = f'invoke {c2}.{n2}{p2[:40]}'
            elif op in (0x35, 0x36, 0x37, 0x38, 0x39, 0x3a, 0x3b, 0x3c, 0x3d):
                off = struct.unpack_from('<h', raw, i*2+2)[0]
                names = {0x35:'if-ge',0x36:'if-gt',0x37:'if-le',0x38:'if-lt',0x39:'if-eq',0x3a:'if-ne',0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez'}
                extra = f'{names[op]} -> {i+off:#x}'
            elif op == 0x28:
                off = struct.unpack_from('<b', raw, i*2+1)[0]
                extra = f'goto -> {i+off:#x}'
            elif op == 0x0d or op == 0x0e:
                extra = 'return'
            elif op == 0x12:
                r8 = (unit >> 8) & 0xf; v8 = (unit >> 12) & 0xf
                extra = f'const/4 v{r8}, {v8 if v8 < 8 else v8 - 16}'
            print(f'  {i:#06x}: op={op:#04x} {extra}')
        # advance
        if op == 0x2c or (op in (0x35,0x36,0x37,0x38,0x39,0x3a)):
            i += 2
        elif op in (0x00,):
            sz = (unit >> 12)
            i += (sz + 1) if sz else 1
        else:
            i += 1 if op not in () else 1
    break
