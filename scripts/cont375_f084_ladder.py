#!/usr/bin/env python3
"""cont375_f084_ladder.py — CORRECT linear disassembly of Lw4;.<init>
from fairymahjong (F-NEW-084 halt frame). Uses the dalvik opcode
unit-size table so payload pseudo-ops (packed-switch/sparse-switch/
fill-array-data) advance correctly."""
import zipfile, struct, io

APK = '/home/z/my-project/apk_cache/com.fairytrick.fairymahjong_5.apk'
WANT_CLASS = 'Lw4;'
WANT_METHOD = '<init>'

# dalvik instruction size table (16-bit code units), index = opcode.
# Derived from AOSP dalvik opcode formats.
SZ = [
 1,1,2,3,1,2,3,1,2,3,1,1,1,1,1,1, 1,1,1,2,2,2,2,2,3,3,3,2,2,2,2,2, # 00-1f
 2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2, # 20-3f
 2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2, # 40-5f
 2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2, # 60-7f
 2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3, # 80-9f
 2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2, # a0-bf
 2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3, # c0-df
 2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2, 2,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3, # e0-ff
]
# pseudo-op sizes computed from their size fields at runtime (0x00 with
# high sub-op): 0x0100 packed-switch, 0x0200 sparse-switch, 0x0300 fill-array-data

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
    return string(struct.unpack_from('<I', d, tof + idx*4)[0])

def fieldid(idx):
    cls, typ, name = struct.unpack_from('<HHI', d, fof + idx*8)
    return f'{typeid(cls)}.{string(name)}:{typeid(typ)}'

def methodid(idx):
    cls, proto, name = struct.unpack_from('<HHI', d, mof + idx*8)
    return f'{typeid(cls)}.{string(name)}'

class_data_off = None
for i in range(cds):
    off = cdo + i*32
    if typeid(struct.unpack_from('<I', d, off)[0]) == WANT_CLASS:
        class_data_off = struct.unpack_from('<I', d, off + 24)[0]
        break
f = io.BytesIO(d); f.seek(class_data_off)
sf, inf_, dm, vm = uleb(f), uleb(f), uleb(f), uleb(f)
def skip_fields(f, n):
    idx = 0
    for _ in range(n):
        idx += uleb(f); uleb(f)
skip_fields(f, sf); skip_fields(f, inf_)
def read_methods(f, n):
    idx = 0; out = []
    for _ in range(n):
        idx += uleb(f); acc = uleb(f); co = uleb(f)
        out.append((idx, acc, co))
    return out
direct = read_methods(f, dm); virtual = read_methods(f, vm)

for idx, acc, co in direct + virtual:
    mname = methodid(idx)
    if not mname.endswith(WANT_METHOD): continue
    reg, ins, outs, tries, dbg, insns = struct.unpack_from('<HHHHII', d, co)
    raw = d[co + 16: co + 16 + insns*2]
    print(f'== {mname} reg={reg} insns={insns}')
    i = 0
    while i < insns:
        unit = struct.unpack_from('<H', raw, i*2)[0]
        op = raw[i*2 + 1]
        ann = ''
        if op == 0x00 and unit >= 0x0100:
            ident = struct.unpack_from('<H', raw, i*2+2)[0]
            if unit == 0x0100: ann = f'packed-switch-payload ident={ident:#x} targets={ident}'
            elif unit == 0x0200: ann = 'sparse-switch-payload'
            elif unit == 0x0300: ann = 'fill-array-data-payload'
            sz = (unit >> 12) & 0xf
            ann += f' total={sz+1} units'
        elif op == 0x1a:
            bidx = struct.unpack_from('<H', raw, i*2+2)[0]
            ann = f'const-string "{string(bidx)[:56]}"'
        elif op == 0x1b:
            bidx = struct.unpack_from('<I', raw, i*2+2)[0]
            ann = f'const-string/jumbo "{string(bidx)[:56]}"'
        elif op == 0x62 or op == 0x60 or op == 0x63 or op == 0x59 or op == 0x5a:
            ann = fieldid(struct.unpack_from('<H', raw, i*2+2)[0])
        elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78):
            ann = 'invoke ' + methodid(struct.unpack_from('<H', raw, i*2+2)[0])
        elif op in (0x35, 0x36, 0x37, 0x38, 0x39, 0x3a):
            off = struct.unpack_from('<h', raw, i*2+2)[0]
            names = {0x35:'if-ge',0x36:'if-gt',0x37:'if-le',0x38:'if-lt',0x39:'if-eq',0x3a:'if-ne'}
            ann = f'{names[op]} -> {i+off:#x}'
        elif op in (0x3b, 0x3c, 0x3d):
            off = struct.unpack_from('<h', raw, i*2+2)[0]
            names = {0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez'}
            ann = f'{names[op]} -> {i+off:#x}'
        elif op == 0x28:
            off = struct.unpack_from('<b', raw, i*2+1)[0]
            ann = f'goto -> {i+off:#x}'
        elif op == 0x29:
            off = struct.unpack_from('<h', raw, i*2+2)[0]
            ann = f'goto/32 -> {i+off:#x}'
        elif op in (0x32, 0x33, 0x34):
            off = struct.unpack_from('<h', raw, i*2+2)[0]
            names = {0x32:'if-eqz',0x33:'if-nez',0x34:'if-ltz'}
            ann = f'{names[op]} -> {i+off:#x}'
        elif op == 0x12:
            r8 = (unit >> 8) & 0xf; v8 = (unit >> 12) & 0xf
            ann = f'const/4 v{r8}, {v8 if v8 < 8 else v8 - 16}'
        elif op == 0x13:
            r8 = struct.unpack_from('<B', raw, i*2+1)[0]
            v32 = struct.unpack_from('<H', raw, i*2+2)[0]
            ann = f'const/16 v{r8}, {v32}'
        elif op in (0xa00 >> 8,):
            pass
        print(f'  {i:#06x}: op={op:#04x} unit={unit:#06x} {ann}')
        # advance
        if op == 0x00 and unit >= 0x0100:
            i += ((unit >> 12) & 0xf) + 1
        else:
            i += SZ[op] if op < len(SZ) else 1
    break
