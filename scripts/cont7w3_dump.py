#!/usr/bin/env python3
"""cont7w3_dump.py — dump one method's bytecode by class+name.
Usage: cont7w3_dump.py <apk> Lcls; name
"""
import sys, zipfile, struct

APK, CLS, METH = sys.argv[1], sys.argv[2], sys.argv[3]

OPNAMES = {0x00:'nop',0x01:'move',0x04:'move-wide',0x07:'move-object',0x0a:'move-result',
0x0b:'move-result-wide',0x0c:'move-result-object',0x0d:'move-exception',0x0e:'return-void',
0x0f:'return',0x10:'return-wide',0x11:'return-object',0x12:'const/4',0x13:'const/16',
0x14:'const',0x15:'const/high16',0x16:'const-wide/16',0x17:'const-wide/32',0x18:'const-wide',
0x19:'const-wide/high16',0x1a:'const-string',0x1b:'const-string/jumbo',0x1c:'const-class',
0x1d:'monitor-enter',0x1e:'monitor-exit',0x1f:'check-cast',0x20:'instance-of',0x21:'array-length',
0x22:'new-instance',0x23:'new-array',0x24:'filled-new-array',0x25:'filled-new-array/range',
0x26:'fill-array-data',0x27:'throw',0x28:'goto',0x29:'goto/16',0x2a:'goto/32',0x2b:'packed-switch',
0x2c:'sparse-switch'}

S = [1]*256
S[0x01]=1; S[0x02]=2; S[0x03]=3   # move, move/from16, move/16
S[0x04]=1; S[0x05]=2; S[0x06]=3   # move-wide family
S[0x07]=1; S[0x08]=2; S[0x09]=3   # move-object family
for o in range(0x0a, 0x13): S[o] = 1
S[0x12] = 1
S[0x13] = 2; S[0x14] = 3; S[0x15] = 2; S[0x16] = 2; S[0x17] = 3; S[0x18] = 5; S[0x19] = 2
S[0x1a] = 2; S[0x1b] = 3; S[0x1c] = 2
S[0x1d] = 1; S[0x1e] = 1
S[0x1f] = 2; S[0x20] = 2; S[0x21] = 1; S[0x22] = 2; S[0x23] = 2
S[0x24] = 3; S[0x25] = 3; S[0x26] = 3
S[0x27] = 1
S[0x28] = 1; S[0x29] = 2; S[0x2a] = 3
S[0x2b] = 3; S[0x2c] = 3
for o in range(0x2d, 0x32): S[o] = 2
for o in range(0x32, 0x3e): S[o] = 2
for o in range(0x44, 0x52): S[o] = 2
for o in range(0x52, 0x5e): S[o] = 2
for o in range(0x5e, 0x6e): S[o] = 2
for o in range(0x6e, 0x73): S[o] = 3
S[0x73] = 1
for o in range(0x74, 0x79): S[o] = 4
for o in range(0x7b, 0x90): S[o] = 1
for o in range(0x90, 0xb0): S[o] = 2
for o in range(0xb0, 0xd0): S[o] = 1
for o in range(0xd0, 0xd8): S[o] = 2
for o in range(0xd8, 0xe3): S[o] = 2
S[0xfa] = 4; S[0xfb] = 4; S[0xfc] = 3; S[0xfd] = 3

BINOPS = {0x90:'add-int',0x91:'sub-int',0x92:'mul-int',0x93:'div-int',0x94:'rem-int',
0x95:'and-int',0x96:'or-int',0x97:'xor-int',0x98:'shl-int',0x99:'shr-int',0x9a:'ushr-int',
0x9b:'add-long',0x9c:'sub-long',0x9d:'mul-long',0x9e:'div-long',0x9f:'rem-long',
0xa0:'add-float',0xa1:'sub-float',0xa2:'mul-float',0xa3:'div-float',0xa4:'rem-float',
0xa5:'add-double',0xa6:'sub-double',0xa7:'mul-double',0xa8:'div-double',0xa9:'rem-double',
0xaa:'add-int/2addr',0xab:'sub-int/2addr',0xac:'mul-int/2addr',0xad:'div-int/2addr',
0xae:'rem-int/2addr',0xaf:'and-int/2addr',0xb0:'or-int/2addr',0xb1:'xor-int/2addr',
0xb2:'shl-int/2addr',0xb3:'shr-int/2addr',0xb4:'ushr-int/2addr',
0xb5:'add-long/2addr',0xb6:'sub-long/2addr',0xb7:'mul-long/2addr',0xb8:'div-long/2addr',
0xb9:'rem-long/2addr',0xba:'and-long/2addr',0xbb:'or-long/2addr',0xbc:'xor-long/2addr',
0xbd:'shl-long/2addr',0xbe:'shr-long/2addr',0xbf:'ushr-long/2addr',
0xc0:'add-float/2addr',0xc1:'sub-float/2addr',0xc2:'mul-float/2addr',0xc3:'div-float/2addr',
0xc4:'rem-float/2addr',0xc5:'add-double/2addr',0xc6:'sub-double/2addr',0xc7:'mul-double/2addr',
0xc8:'div-double/2addr',0xc9:'rem-double/2addr'}
for k,v in BINOPS.items(): OPNAMES[k]=v
IGET = {0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',0x56:'iget-byte',
0x57:'iget-char',0x58:'iget-short',0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',
0x5c:'iput-boolean',0x5d:'iput-byte',0x5e:'iput-char',0x5f:'iput-short'}
for k,v in IGET.items(): OPNAMES[k]=v
SGET = {0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x63:'sget-boolean',0x64:'sget-byte',
0x65:'sget-char',0x66:'sget-short',0x67:'sput',0x68:'sput-wide',0x69:'sput-object',
0x6a:'sput-boolean',0x6b:'sput-byte',0x6c:'sput-char',0x6d:'sput-short'}
for k,v in SGET.items(): OPNAMES[k]=v
INVOKE = {0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
0x71:'invoke-static',0x72:'invoke-interface'}
for k,v in INVOKE.items(): OPNAMES[k]=v
for o in range(0x74,0x79): OPNAMES[o]=INVOKE.get(0x6e+ (o-0x74),'invoke-range')
COND = {0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',0x37:'if-le',
0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez'}
for k,v in COND.items(): OPNAMES[k]=v
CMP = {0x2d:'cmpl-float',0x2e:'cmpg-float',0x2f:'cmpl-double',0x30:'cmpg-double',0x31:'cmp-long'}
for k,v in CMP.items(): OPNAMES[k]=v
AGET = {0x44:'aget',0x45:'aget-wide',0x46:'aget-object',0x47:'aget-boolean',0x48:'aget-byte',
0x49:'aget-char',0x4a:'aget-short',0x4b:'aput',0x4c:'aput-wide',0x4d:'aput-object',
0x4e:'aput-boolean',0x4f:'aput-byte',0x50:'aput-char',0x51:'aput-short'}
for k,v in AGET.items(): OPNAMES[k]=v
UNOP = {}
for o in range(0x7b,0x90): UNOP[o]=f'unop_{o:02x}'
for k,v in UNOP.items(): OPNAMES[k]=v

if APK.endswith('.dex'):
    b = open(APK,'rb').read()
else:
    b = zipfile.ZipFile(APK).read('classes.dex')

def uleb(off):
    r=0;s=0
    while True:
        by=b[off];off+=1
        r|=(by&0x7f)<<s;s+=7
        if not by&0x80: return r,off

string_ids_size, string_ids_off = struct.unpack_from('<II', b, 0x38)
type_ids_size, type_ids_off = struct.unpack_from('<II', b, 0x40)
field_ids_size, field_ids_off = struct.unpack_from('<II', b, 0x50)
method_ids_size, method_ids_off = struct.unpack_from('<II', b, 0x58)
class_defs_size, class_defs_off = struct.unpack_from('<II', b, 0x60)
proto_ids_off = struct.unpack_from('<I', b, 0x4c)[0]

def getstr(i):
    off = struct.unpack_from('<I', b, string_ids_off+4*i)[0]
    l, off = uleb(off)
    return b[off:b.index(b'\x00',off)].decode('utf-8','replace')
def gettype(i):
    if i==0xffffffff: return '<none>'
    return getstr(struct.unpack_from('<I', b, type_ids_off+4*i)[0])
def getfield(i):
    ci, ti, ni = struct.unpack_from('<HHI', b, field_ids_off+8*i)
    return f"{gettype(ci)}.{getstr(ni)}:{gettype(ti)}"
def getmeth(i):
    ci, pi, ni = struct.unpack_from('<HHI', b, method_ids_off+8*i)
    return f"{gettype(ci)}.{getstr(ni)}"
def meth_full(i):
    ci, pi, ni = struct.unpack_from('<HHI', b, method_ids_off+8*i)
    return getmeth(i)

def fmt(insns, base_off, insns_size):
    out=[]
    ip=0
    end=insns_size
    units=struct.unpack_from(f'<{insns_size}H', b, base_off)
    while ip<end:
        unit=units[ip]
        op=unit&0xff
        # payload pseudo-structures (ident in HIGH byte)
        if unit==0x0100:  # packed-switch payload
            size=units[ip+1]
            total=4+2*size
            out.append(f"  {ip}: <packed-switch payload size={size} end={ip+total}>")
            ip+=total; continue
        if unit==0x0200:  # sparse-switch payload
            size=units[ip+1]
            total=2+4*size
            out.append(f"  {ip}: <sparse-switch payload size={size} end={ip+total}>")
            ip+=total; continue
        if unit==0x0300:  # fill-array-data payload
            ew=units[ip+1]; size=units[ip+2]|(units[ip+3]<<16)
            total=4+(size*ew+1)//2
            out.append(f"  {ip}: <array-data payload ew={ew} size={size} end={ip+total}>")
            ip+=total; continue
        name=OPNAMES.get(op, f'op_{op:02x}')
        pc=ip
        try:
            sz=S[op]
        except IndexError:
            sz=1
        if op==0x1a:  # const-string
            vA=(units[ip]>>8)&0xf; tidx=units[ip+1]
            out.append(f"  {pc}: const-string v{vA}, '{getstr(tidx)}'")
        elif op in (0x1c,0x1f,0x20,0x22,0x23):
            tidx=units[ip+1]
            va=(units[ip]>>8)&0xff
            if op in (0x1c,0x1f): out.append(f"  {pc}: {name} v{va}, {gettype(tidx)}")
            elif op==0x20:
                vb=(units[ip+1]>>8)&0xf
                out.append(f"  {pc}: instance-of v{va}, v{vb}, {gettype(tidx)}")
            elif op==0x23: out.append(f"  {pc}: new-array v{va}, {gettype(tidx)}")
            else: out.append(f"  {pc}: {name} v{va} (sz={S[op]})")
        elif op==0x27:
            va=(units[ip]>>8)&0xf
            out.append(f"  {pc}: throw v{va}")
        elif op in (0x28,):
            off8=units[ip]>>8
            if off8>127: off8-=256
            out.append(f"  {pc}: goto -> {pc+off8}")
        elif op==0x29:
            off16=units[ip+1]
            if off16>32767: off16-=65536
            out.append(f"  {pc}: goto/16 -> {pc+off16}")
        elif op==0x2a:
            off32=units[ip+1]|(units[ip+2]<<16)
            out.append(f"  {pc}: goto/32 -> {pc+off32}")
        elif op in COND:
            va=(units[ip]>>8)&0xf; vb=(units[ip]>>12)&0xf
            off=units[ip+1]
            if off>32767: off-=65536
            out.append(f"  {pc}: {name} v{va}, v{vb} -> {pc+off}")
        elif op in COND and op>=0x38:
            pass
        elif op in (0x38,0x39,0x3a,0x3b,0x3c,0x3d):
            va=(units[ip]>>8)&0xff
            off=units[ip+1]
            if off>32767: off-=65536
            out.append(f"  {pc}: {name} v{va} -> {pc+off}")
        elif op in IGET.values() or op in IGET:
            va=(units[ip]>>8)&0xf; vb=(units[ip]>>12)&0xf; fidx=units[ip+1]
            out.append(f"  {pc}: {name} v{va}, v{vb}, {getfield(fidx)}")
        elif op in SGET.values() or op in SGET:
            va=(units[ip]>>8)&0xff; fidx=units[ip+1]
            out.append(f"  {pc}: {name} v{va}, {getfield(fidx)}")
        elif op in INVOKE:
            cnt=(units[ip]>>12)&0xf; midx=units[ip+1]
            regs=[(units[ip]>>8)&0xf]
            if cnt>1: regs.append(units[ip+2]&0xf)
            if cnt>2: regs.append((units[ip+2]>>4)&0xf)
            if cnt>3: regs.append(units[ip+2]>>12)
            if cnt>4: regs.append(units[ip+3]&0xf)
            out.append(f"  {pc}: {name} {{{','.join('v'+str(r) for r in regs[:cnt])}}}, {getmeth(midx)}")
        elif op in (0x74,0x75,0x76,0x77,0x78):
            cnt=(units[ip]>>12)&0xf; midx=units[ip+1]; start=units[ip+2]
            out.append(f"  {pc}: {name}/range {{v{start}..v{start+cnt-1}}}, {getmeth(midx)}")
        elif op in (0x52,0x54,0x59,0x5b) or (0x52<=op<=0x5f) or (0x60<=op<=0x6d):
            pass
        elif op in (0x32,0x33,0x34,0x35,0x36,0x37):
            pass
        elif op in (0x44,0x45,0x46,0x47,0x48,0x49,0x4a,0x4b,0x4c,0x4d,0x4e,0x4f,0x50,0x51):
            va=units[ip]&0xf; vb=(units[ip]>>4)&0xf; vc=(units[ip]>>8)&0xf
            out.append(f"  {pc}: {name} v{va}, v{vb}, v{vc}")
        elif op in (0x0a,0x0b,0x0c,0x0d):
            va=(units[ip]>>8)&0xf; vb=(units[ip]>>12)&0xf
            out.append(f"  {pc}: {name} v{va}, v{vb}")
        elif op in (0x01,0x04,0x07):
            va=(units[ip]>>8)&0xf; vb=(units[ip]>>12)&0xf
            out.append(f"  {pc}: {name} v{va}, v{vb}")
        elif op==0x12:
            va=(units[ip]>>8)&0xf; lit=(units[ip]>>12)&0xf
            if lit>7: lit-=16
            out.append(f"  {pc}: const/4 v{va}, {lit}")
        elif op==0x13:
            va=units[ip]&0xf; v=units[ip+1]
            if v>32767: v-=65536
            out.append(f"  {pc}: const/16 v{va}, {v}")
        elif op==0x14:
            va=units[ip]&0xf; v=units[ip+1]|(units[ip+2]<<16)
            out.append(f"  {pc}: const v{va}, {v}")
        elif op in (0x0f,0x11,0x0e,0x10):
            if op==0x0e: out.append(f"  {pc}: return-void")
            else:
                va=(units[ip]>>8)&0xf
                out.append(f"  {pc}: {name} v{va}")
        else:
            out.append(f"  {pc}: {name} ({sz} units)")
        ip+=sz
    return out

printed=0
for ci in range(class_defs_size):
    coff = class_defs_off + ci*32
    cls_idx, access, superclass, interfaces_off, srcf, ann, class_data_off, sval = \
        struct.unpack_from('<8I', b, coff)
    cls=gettype(cls_idx)
    if cls!=CLS: continue
    p=class_data_off
    sf,p=uleb(p); ifc,p=uleb(p); dmc,p=uleb(p); vmc,p=uleb(p)
    for _ in range(sf):
        _,p=uleb(p); _,p=uleb(p)
    for _ in range(ifc):
        _,p=uleb(p); _,p=uleb(p)
    for section,count in (('direct',dmc),('virtual',vmc)):
        prev=0
        for _ in range(count):
            d,p=uleb(p); a,p=uleb(p)
            midx=prev+d; prev=midx
            c2,p=uleb(p)
            code_off=c2
            if not code_off or code_off+16>len(b): continue
            regs,ins,outs,tries,dbg,insns_size=struct.unpack_from('<HHHHII', b, code_off)
            if getstr(struct.unpack_from('<H', b, method_ids_off+8*midx+4)[0])!=METH: continue
            # name check
            ci2,pi2,ni2=struct.unpack_from('<HHI', b, method_ids_off+8*midx)
            if getstr(ni2)!=METH: continue
            print(f"===== {cls} ({section}) {meth_full(midx)} regs={regs} ins={ins} =====")
            for line in fmt(b, code_off+16, insns_size):
                print(line)
            printed+=1
print(f"printed {printed}")
