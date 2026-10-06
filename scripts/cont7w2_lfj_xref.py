#!/usr/bin/env python3
"""cont7w2_lfj_xref.py — Lfj; (tracking-state holder) construction + method call sites."""
import zipfile, struct

z = zipfile.ZipFile('upload/canonical_apks/io.github.yamin8000.dooz_23.apk')
b = z.read('classes.dex')

SIZES = [1]*256
for o in range(0x01,0x0a): SIZES[o]=1
for o in range(0x0a,0x13): SIZES[o]=1
SIZES[0x13]=2; SIZES[0x14]=3; SIZES[0x15]=2
SIZES[0x16]=2; SIZES[0x17]=3; SIZES[0x18]=5; SIZES[0x19]=2
SIZES[0x1a]=2; SIZES[0x1b]=3; SIZES[0x1c]=2
SIZES[0x1d]=1; SIZES[0x1e]=1
SIZES[0x1f]=2; SIZES[0x20]=2; SIZES[0x21]=1; SIZES[0x22]=2; SIZES[0x23]=2
SIZES[0x24]=3; SIZES[0x25]=3; SIZES[0x26]=3
SIZES[0x27]=1
SIZES[0x28]=1; SIZES[0x29]=2; SIZES[0x2a]=3
SIZES[0x2b]=3; SIZES[0x2c]=3
for o in range(0x2d,0x32): SIZES[o]=2
for o in range(0x32,0x3e): SIZES[o]=2
for o in range(0x3e,0x44): SIZES[o]=1
for o in range(0x44,0x52): SIZES[o]=2
for o in range(0x52,0x5e): SIZES[o]=2
for o in range(0x5e,0x6e): SIZES[o]=2
for o in range(0x6e,0x73): SIZES[o]=3
SIZES[0x73]=1
for o in range(0x74,0x79): SIZES[o]=4
for o in range(0x7b,0x90): SIZES[o]=1
for o in range(0x90,0xb0): SIZES[o]=2
for o in range(0xb0,0xd0): SIZES[o]=1
for o in range(0xd0,0xd8): SIZES[o]=2
for o in range(0xd8,0xe3): SIZES[o]=2
SIZES[0xfa]=4; SIZES[0xfb]=4; SIZES[0xfc]=3; SIZES[0xfd]=3

def uleb(off):
    r=0;s=0
    while True:
        by=b[off];off+=1;r|=(by&0x7f)<<s
        if not (by&0x80):break
        s+=7
    return r,off

string_ids_size,string_ids_off=struct.unpack_from('<II',b,56)
type_ids_size,type_ids_off=struct.unpack_from('<II',b,64)
method_ids_size,method_ids_off=struct.unpack_from('<II',b,88)
class_defs_size,class_defs_off=struct.unpack_from('<II',b,96)

def gs(i):
    do,=struct.unpack_from('<I',b,string_ids_off+i*4)
    n,off=uleb(do)
    e=b.index(b'\x00',off)
    return b[off:e].decode('utf-8','replace')

def gt(i):
    si,=struct.unpack_from('<I',b,type_ids_off+i*4)
    return gs(si)

tidx=None
for i in range(type_ids_size):
    if gt(i)=='Lfj;': tidx=i; break

targets_m=set()
for i in range(method_ids_size):
    cls,proto,name=struct.unpack_from('<HHI',b,method_ids_off+i*8)
    if gt(cls)=='Lfj;' and gs(name) in ('a','b'):
        targets_m.add((i, gs(name)))

def parse_cd(off):
    sf,off=uleb(off); inf,off=uleb(off); dm,off=uleb(off); vm,off=uleb(off)
    for _ in range(sf):
        _,off=uleb(off); _,off=uleb(off)
    for _ in range(inf):
        _,off=uleb(off); _,off=uleb(off)
    out=[]; midx=0
    for _ in range(dm):
        d,off=uleb(off);midx+=d;acc,off=uleb(off);coff,off=uleb(off)
        out.append(('direct',midx,acc,coff))
    midx=0
    for _ in range(vm):
        d,off=uleb(off);midx+=d;acc,off=uleb(off);coff,off=uleb(off)
        out.append(('virtual',midx,acc,coff))
    return out

for ci in range(class_defs_size):
    off=class_defs_off+ci*32
    cls_idx,access,sup,itf,src,ann,cd,sv=struct.unpack_from('<8I',b,off)
    if cd==0: continue
    cls=gt(cls_idx)
    for kind,midx,acc,coff in parse_cd(cd):
        if coff==0: continue
        regs,ins,outs,tries,dbg,insns_size=struct.unpack_from('<HHHHII',b,coff)
        insns_off=coff+16
        pc=0; newpcs=[]; callpcs=[]
        while pc<insns_size:
            u0,=struct.unpack_from('<H',b,insns_off+pc*2)
            op=u0&0xff
            if u0==0x0100:
                size,=struct.unpack_from('<H',b,insns_off+(pc+1)*2); pc+=4+2*size; continue
            if u0==0x0200:
                size,=struct.unpack_from('<H',b,insns_off+(pc+1)*2); pc+=2+4*size; continue
            if u0==0x0300:
                ew,size=struct.unpack_from('<HH',b,insns_off+(pc+1)*2); pc+=4+(size*ew+1)//2; continue
            if op==0x22:
                t,=struct.unpack_from('<H',b,insns_off+(pc+1)*2)
                if t==tidx: newpcs.append(pc)
                pc+=2; continue
            if op in range(0x6e,0x73):
                m,=struct.unpack_from('<H',b,insns_off+(pc+1)*2)
                for mi,mn in targets_m:
                    if mi==m: callpcs.append((pc,mn))
                pc+=3; continue
            if op in range(0x74,0x79):
                m,=struct.unpack_from('<H',b,insns_off+(pc+1)*2)
                for mi,mn in targets_m:
                    if mi==m: callpcs.append((pc,mn))
                pc+=4; continue
            if op in (0x2b,0x2c):
                pc+=3; continue
            if op in (0x1a,0x1c,0x1f):
                pc+=2; continue
            pc+=SIZES[op]
        if newpcs or callpcs:
            try:
                c2,p2,n2=struct.unpack_from('<HHI',b,method_ids_off+midx*8)
                mname=gs(n2)
            except Exception:
                mname=f"midx={midx}"
            print(f"{cls} ({kind}) .{mname}  new@{newpcs}  call@{callpcs}")
