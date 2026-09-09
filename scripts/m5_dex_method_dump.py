#!/usr/bin/env python3
"""M5: ground-truth method dump for a class from classes.dex (raw DEX parse)."""
import zipfile, sys, struct

APK = '/home/z/my-project/apk_cache/corpus/dooz.apk'
CLS = sys.argv[1] if len(sys.argv) > 1 else 'LY1/j;'

raw = zipfile.ZipFile(APK).read('classes.dex')
u32 = lambda o: struct.unpack_from('<I', raw, o)[0]
u16 = lambda o: struct.unpack_from('<H', raw, o)[0]
u64 = lambda o: struct.unpack_from('<Q', raw, o)[0]
uleb = lambda o: 0

def read_uleb(off):
    result, shift, b = 0, 0, 0
    while True:
        b = raw[off]; off += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return result, off

# header
string_ids = u32(0x38); string_off = u32(0x3c)
type_ids = u32(0x40); type_off = u32(0x44)
proto_ids = u32(0x48); proto_off = u32(0x4c)
field_ids = u32(0x50); field_off = u32(0x54)
method_ids = u32(0x58); method_off = u32(0x5c)
class_defs = u32(0x60); class_off = u32(0x64)

def get_str(idx):
    off = u32(string_off + idx*4)
    n, o = read_uleb(off)
    end = raw.index(b'\x00', o)
    return raw[o:end].decode('utf-8', 'replace')

def get_type(idx):
    return get_str(u32(type_off + idx*4))

def get_field(idx):
    cls = get_type(u16(field_off + idx*8))
    typ = get_type(u16(field_off + idx*8 + 2))
    name = get_str(u32(field_off + idx*8 + 4))
    return f"{cls}.{name} : {typ}"

def get_method(idx):
    cls = get_type(u16(method_off + idx*8))
    proto = u16(method_off + idx*8 + 2)
    name = get_str(u32(method_off + idx*8 + 4))
    ret = get_type(u16(proto_off + proto*12 + 4))
    po = u32(proto_off + proto*12 + 8)
    nparams = u32(po) if po else 0
    params = ''.join(get_type(u16(po + 4 + i*2)) for i in range(nparams))
    return f"{cls}.{name}({params}){ret}"

# find class def
target = None
for i in range(class_defs):
    co = class_off + i*32
    if get_type(u32(co)) == CLS:
        target = co
        break
if target is None:
    print(f'class {CLS} NOT FOUND'); sys.exit(1)

print(f'=== {CLS} class_data_off=0x{u32(target+24):x} ===')
cdo = u32(target+24)
static_f, o = read_uleb(cdo)
inst_f, o = read_uleb(o)
direct_m, o = read_uleb(o)
virtual_m, o = read_uleb(o)
fidx = 0
for kind, count in (('static', static_f), ('instance', inst_f)):
    fidx = 0
    for _ in range(count):
        d, o = read_uleb(o); fidx += d
        acc, o = read_uleb(o)
        print(f'  {kind} field: {get_field(fidx)} acc=0x{acc:x}')
for kind, count in (('direct', direct_m), ('virtual', virtual_m)):
    midx = 0
    for _ in range(count):
        d, o = read_uleb(o); midx += d
        acc, o = read_uleb(o)
        cregs, o = read_uleb(o)
        if acc & 0x400:
            print(f'  {kind} method: {get_method(midx)} acc=0x{acc:x} ABSTRACT')
        else:
            print(f'  {kind} method: {get_method(midx)} acc=0x{acc:x} code_off=0x{cregs:x}')
