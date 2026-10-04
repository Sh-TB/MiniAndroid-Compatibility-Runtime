#!/usr/bin/env python3
"""cont375_lm_dump.py — disassemble Lm;.equals/.hashCode/.<init>/.a
(fairymahjong tile-position value class) with the correct size table."""
import zipfile, struct, io

APK = '/home/z/my-project/apk_cache/com.fairytrick.fairymahjong_5.apk'

SZ = [1,1,2,3,1,2,3,1,2,3,1,1,1,1,1,1,
      1,1,1,2,2,2,2,2,3,3,3,2,2,2,2,2] + [2]*(0x74-0x20) + [3,3,3,3,3] + [1,1] + [2]*(0x100-0x7a)

z = zipfile.ZipFile(APK)
d = z.read('classes.dex')
ssz, sof = struct.unpack_from('<II', d, 0x38)
tsz, tof = struct.unpack_from('<II', d, 0x40)
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
    f = io.BytesIO(d); f.seek(off); n = uleb(f)
    return f.read(n).decode('utf-8', 'replace')

def typeid(idx):
    return string(struct.unpack_from('<I', d, tof + idx*4)[0])

def fieldid(idx):
    cls, typ, name = struct.unpack_from('<HHI', d, fof + idx*8)
    return f'{typeid(cls)}.{string(name)}:{typeid(typ)}'

def methodid(idx):
    cls, proto, name = struct.unpack_from('<HHI', d, mof + idx*8)
    return f'{typeid(cls)}.{string(name)}'

for i in range(cds):
    off = cdo + i*32
    if typeid(struct.unpack_from('<I', d, off)[0]) == 'Lm;':
        cdo2 = struct.unpack_from('<I', d, off + 24)[0]
        break
f = io.BytesIO(d); f.seek(cdo2)
sf, inf_, dm, vm = uleb(f), uleb(f), uleb(f), uleb(f)
for _ in range(sf): uleb(f); uleb(f)
for _ in range(inf_): uleb(f); uleb(f)
def rms(f, n):
    idx = 0; out = []
    for _ in range(n):
        idx += uleb(f); acc = uleb(f); co = uleb(f)
        out.append((idx, acc, co))
    return out

for idx, acc, co in rms(f, dm) + rms(f, vm):
    mname = methodid(idx)
    short = mname.split('.')[-1]
    if short not in ('equals', 'hashCode', '<init>', 'a', '<clinit>'): continue
    reg, ins, outs, tries, dbg, insns = struct.unpack_from('<HHHHII', d, co)
    base = co + 16
    print(f'== {mname} reg={reg} ins={ins} insns={insns}')
    raw = d[base: base + insns*2]
    i = 0
    while i < insns:
        unit = struct.unpack_from('<H', raw, i*2)[0]
        op = raw[i*2]
        sz = SZ[op] if op < len(SZ) else 1
        ann = ''
        if op == 0x00 and unit >= 0x0100:
            sz = ((unit >> 12) & 0xf) + 1
            ann = 'PAYLOAD'
        elif op == 0x1a:
            ann = f'const-string "{string(struct.unpack_from("<H", raw, i*2+2)[0])[:40]}"'
        elif op in (0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f,
                    0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d):
            ann = fieldid(struct.unpack_from('<H', raw, i*2+2)[0])
        elif op in (0x6e,0x6f,0x70,0x71,0x72,0x74,0x75,0x76,0x77,0x78):
            ann = 'invoke ' + methodid(struct.unpack_from('<H', raw, i*2+2)[0])
        elif 0x32 <= op <= 0x37:
            o = struct.unpack_from('<h', raw, i*2+2)[0]
            a_ = (unit >> 12) & 0xF; b_ = (unit >> 8) & 0xF
            nm = {0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',0x37:'if-le'}[op]
            ann = f'{nm} v{a_}, v{b_} -> {i+o:#x}'
        elif 0x38 <= op <= 0x3d:
            o = struct.unpack_from('<h', raw, i*2+2)[0]
            nm = {0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez'}[op]
            ann = f'{nm} v{(unit>>8)&0xFF} -> {i+o:#x}'
        elif op == 0x28:
            o = struct.unpack_from('<b', raw, i*2+1)[0]
            ann = f'goto -> {i+o:#x}'
        elif op == 0x12:
            ann = f'const/4 v{(unit>>8)&0xF}, {(unit>>12)&0xF}'
        elif op == 0x13:
            ann = f'const/16 v{raw[i*2]}, {struct.unpack_from("<h", raw, i*2+2)[0]}'
        elif op == 0x14:
            ann = f'const v{raw[i*2]}, {struct.unpack_from("<i", raw, i*2+2)[0]}'
        elif op == 0x22:
            ann = f'new-instance {typeid(struct.unpack_from("<H", raw, i*2+2)[0])}'
        print(f'  {i:#04x}: op={op:#04x} u={unit:#06x} {ann}')
        i += sz
