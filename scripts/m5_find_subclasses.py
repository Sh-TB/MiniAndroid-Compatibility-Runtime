#!/usr/bin/env python3
"""M5: find all subclasses of a class + their method overrides (ground truth)."""
import zipfile, sys, struct

APK = '/home/z/my-project/apk_cache/corpus/dooz.apk'
SUPER = sys.argv[1] if len(sys.argv) > 1 else 'LY1/j;'
raw = zipfile.ZipFile(APK).read('classes.dex')
u32 = lambda o: struct.unpack_from('<I', raw, o)[0]
u16 = lambda o: struct.unpack_from('<H', raw, o)[0]
string_ids=u32(0x38); string_off=u32(0x3c); type_ids=u32(0x40); type_off=u32(0x44)
proto_ids=u32(0x48); proto_off=u32(0x4c)
field_ids=u32(0x50); field_off=u32(0x54)
method_ids=u32(0x58); method_off=u32(0x5c)
class_defs=u32(0x60); class_off=u32(0x64)
def read_uleb(off):
    r,s=0,0
    while True:
        b=raw[off]; off+=1; r|=(b&0x7f)<<s
        if not (b&0x80): break
        s+=7
    return r,off
def get_str(idx):
    off=u32(string_off+idx*4)
    n,o=read_uleb(off)
    end=raw.index(b'\x00',o)
    return raw[o:end].decode('utf-8','replace')
def get_type(i): return get_str(u32(type_off+i*4))
def get_method_name(idx): return get_str(u32(method_off+idx*8+4))
def get_method_proto(idx):
    proto=u16(method_off+idx*8+2)
    ret=get_type(u16(proto_off+proto*12+4))
    po=u32(proto_off+proto*12+8)
    n=u32(po) if po else 0
    params=''.join(get_type(u16(po+4+i*2)) for i in range(n))
    return f"({params}){ret}"
def get_field(idx):
    typ=get_type(u16(field_off+idx*8+2))
    name=get_str(u32(field_off+idx*8+4))
    return f"{name} : {typ}"

for i in range(class_defs):
    co=class_off+i*32
    if get_type(u32(co+4))==SUPER:
        cls=get_type(u32(co))
        cdo=u32(co+24)
        sf,o=read_uleb(cdo); inf,o=read_uleb(o); dm,o=read_uleb(o); vm,o=read_uleb(o)
        fields=[]
        fidx=0
        for _ in range(sf):
            d,o=read_uleb(o); fidx+=d
            acc,o=read_uleb(o)
            fields.append(get_field(fidx))
        fidx=0
        for _ in range(inf):
            d,o=read_uleb(o); fidx+=d
            acc,o=read_uleb(o)
            fields.append(get_field(fidx))
        methods=[]
        midx=0
        for _ in range(dm):
            d,o=read_uleb(o); midx+=d
            acc,o=read_uleb(o)
            cregs,o=read_uleb(o)
            methods.append((get_method_name(midx), get_method_proto(midx), acc, cregs))
        midx=0
        for _ in range(vm):
            d,o=read_uleb(o); midx+=d
            acc,o=read_uleb(o)
            cregs,o=read_uleb(o)
            methods.append((get_method_name(midx), get_method_proto(midx), acc, cregs))
        print(f"SUBCLASS {cls} (fields: {fields})")
        for name, proto, acc, cregs in methods:
            if acc & 0x400:
                print(f"    {name}{proto} ABSTRACT")
            else:
                print(f"    {name}{proto} code_off=0x{cregs:x}")
