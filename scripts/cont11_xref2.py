#!/usr/bin/env python3
"""cont11_xref.py — whole-APK cross-reference scanner (W7).
Finds every method that references a target type via:
  - new-instance type@T
  - invoke-* with method_id class == T
  - const-class/check-cast/instance-of/filled-new-array type@T
Usage: cont11_xref.py <apk> "Ljt1;"
"""
import sys, zipfile, struct

def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]

SIZES=[1]*256
for o in range(0x01,0x13): SIZES[o]=1
SIZES[0x12]=1; SIZES[0x13]=2; SIZES[0x14]=3; SIZES[0x15]=2
SIZES[0x16]=2; SIZES[0x17]=3; SIZES[0x18]=5; SIZES[0x19]=2
SIZES[0x1a]=2; SIZES[0x1b]=3; SIZES[0x1c]=2; SIZES[0x1d]=1; SIZES[0x1e]=1
SIZES[0x1f]=2; SIZES[0x20]=2; SIZES[0x21]=1; SIZES[0x22]=2; SIZES[0x23]=2
SIZES[0x24]=3; SIZES[0x25]=3; SIZES[0x26]=3; SIZES[0x27]=1
SIZES[0x28]=1; SIZES[0x29]=2; SIZES[0x2a]=3; SIZES[0x2b]=3; SIZES[0x2c]=3
for o in range(0x2d,0x3e): SIZES[o]=2
for o in range(0x3e,0x44): SIZES[o]=1
for o in range(0x44,0x52): SIZES[o]=2
for o in range(0x52,0x6e): SIZES[o]=2
for o in range(0x6e,0x73): SIZES[o]=3
SIZES[0x73]=1
for o in range(0x74,0x79): SIZES[o]=4
SIZES[0x79]=1; SIZES[0x7a]=1
for o in range(0xfa,0x100): SIZES[o]=3

def load_dexes(apk):
    out=[]
    with zipfile.ZipFile(apk) as z:
        for n in sorted(z.namelist()):
            if n.startswith('classes') and n.endswith('.dex'):
                out.append((n, z.read(n)))
    return out

def parse_strings(d):
    toff=u32(d,0x3c); cnt=u32(d,0x38)
    strs=[]
    for i in range(cnt):
        p=u32(d,toff+4*i); r=0; s=0
        while True:
            b=d[p]; p+=1; r|=(b&0x7f)<<s; s+=7
            if not b&0x80: break
        strs.append(d[p:p+r].decode('utf-8','replace'))
    return strs

def parse_typeids(d, strs):
    off=u32(d,0x44); cnt=u32(d,0x40)
    return [strs[u32(d,off+4*i)] for i in range(cnt)]

def parse_methodids(d, strs, types):
    off=u32(d,0x5c); cnt=u32(d,0x58); poff=u32(d,0x4c)
    ms=[]
    for i in range(cnt):
        e=off+8*i
        cls=types[u16(d,e)]; name=strs[u32(d,e+4)]
        ret=types[u32(d,poff+12*u16(d,e+2)+4)]
        ms.append((cls,name,ret))
    return ms

def parse_classes(d):
    off=u32(d,0x64); cnt=u32(d,0x60)
    return [(u32(d,off+32*i), u32(d,off+32*i+24)) for i in range(cnt)]

def parse_class_data(d, cdoff):
    p=cdoff
    def uleb():
        nonlocal p
        r=0;s=0
        while True:
            b=d[p]; p+=1; r|=(b&0x7f)<<s; s+=7
            if not b&0x80: break
        return r
    sf=uleb(); inf=uleb(); dm=uleb(); vm=uleb()
    for _ in range(sf+inf): uleb(); uleb()
    methods=[]; midx=0
    for _ in range(dm):
        midx+=uleb(); uleb(); coff=uleb()
        methods.append((midx,coff))
    midx=0
    for _ in range(vm):
        midx+=uleb(); uleb(); coff=uleb()
        methods.append((midx,coff))
    return methods

def scan_code(d, code_off, tidx, nmids):
    hits=[]
    if code_off==0: return hits
    insns_sz=u32(d,code_off+12); insns_off=code_off+16
    n=insns_sz
    def w(i): return u16(d,insns_off+2*i)
    i=0
    while i<n:
        op=w(i)&0xff
        if op==0x22:
            if w(i+1)==tidx: hits.append(('new',0))
            i+=2
        elif op in (0x1c,0x1f,0x20):
            if w(i+1)==tidx: hits.append(('typeref',0))
            i+=2
        elif (0x6e<=op<=0x72) or (0x74<=op<=0x78):
            m=w(i+1)
            if m<nmids: hits.append(('call',m))
            i+=SIZES[op]
        elif op in (0x24,0x25):
            if w(i+1)==tidx: hits.append(('typeref',0))
            i+=3
        elif op==0x00:
            ident=(w(i)>>8)&0xff
            if ident==0x01: i+=2*w(i+1)+4      # packed-switch: size u16@+1, targets size*2 words + 4
            elif ident==0x02: i+=4*w(i+1)+2    # sparse-switch: size u16@+1, keys+vals size*4 words + 2
            elif ident==0x03:                   # fill-array-data: ew u16@+1, size u32@+2
                ew=w(i+1); sz=u32(d,insns_off+2*(i+2))
                i+=((sz*ew+1)//2)+4
            else: i+=1
        else:
            i+=SIZES[op] if SIZES[op] else 1
    return hits

def main():
    apk, target = sys.argv[1], sys.argv[2]
    for name, d in load_dexes(apk):
        strs=parse_strings(d); types=parse_typeids(d,strs)
        if target not in types: continue
        tidx=types.index(target)
        mids=parse_methodids(d,strs,types)
        classes=parse_classes(d)
        print(f"== {name}: {target} type_idx={tidx}")
        for cls_idx, cdoff in classes:
            if cls_idx==tidx:
                for midx,coff in parse_class_data(d,cdoff):
                    cls,nm,ret=mids[midx]
                    print(f"   DECL {nm} -> {ret} code_off={coff}")
        for cls_idx, cdoff in classes:
            cls_name=types[cls_idx]
            for midx,coff in parse_class_data(d,cdoff):
                if coff==0: continue
                if midx>=len(mids):
                    print(f"   WARN midx={midx} OOR in {cls_name} cdoff={cdoff}")
                    continue
                mcls,mnm,mret=mids[midx]
                for kind,arg in scan_code(d,coff,tidx,len(mids)):
                    if kind=='new':
                        print(f"   REF new-instance  {cls_name}.{mnm}")
                    elif kind=='typeref':
                        print(f"   REF type-ref      {cls_name}.{mnm}")
                    elif kind=='call':
                        c2,n2,r2=mids[arg]
                        if c2==target:
                            print(f"   REF call {n2}   {cls_name}.{mnm}")

if __name__=='__main__':
    main()
