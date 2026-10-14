#!/usr/bin/env python3
"""cont11_rawscan.py — decode every instruction of ONE method correctly.
Usage: cont11_rawscan.py <apk> <Lcls;> <method>
Prints pc, op name, registers, and resolved field/method refs.
"""
import sys, zipfile, struct

apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]

zf = zipfile.ZipFile(apk)

def u4(d,o): return struct.unpack_from('<I', d, o)[0]
def u2(d,o): return struct.unpack_from('<H', d, o)[0]

def run(dexname, data):
    string_off = u4(data,0x3c); type_off = u4(data,0x44)
    proto_off = u4(data,0x4c); field_off = u4(data,0x54)
    meth_off = u4(data,0x5c); cds = u4(data,0x60); cdo = u4(data,0x64)

    def gs(i):
        o = u4(data,string_off+4*i); n=0; s=0; p=o
        while True:
            b=data[p]; n|=(b&0x7f)<<s; s+=7; p+=1
            if not (b&0x80): break
        raw=data[p:p+n]; out=[]; i=0
        while i<len(raw):
            c=raw[i]
            if c==0: break
            if c<0x80: out.append(chr(c)); i+=1
            elif c<0xe0: out.append(chr(((c&0x1f)<<6)|(raw[i+1]&0x3f))); i+=2
            else: out.append(chr(((c&0x0f)<<12)|((raw[i+1]&0x3f)<<6)|(raw[i+2]&0x3f))); i+=3
        return ''.join(out)
    def ts(i): return gs(u4(data,type_off+4*i))
    def mi(i):
        o=meth_off+8*i; c=ts(u2(data,o)); n=gs(u4(data,o+4)); pr=u2(data,o+2)
        po=proto_off+12*pr; pof=u4(data,po+8); ps=''
        if pof:
            for k in range(u4(data,pof)): ps+=ts(u2(data,pof+4+2*k))
        return c,n,'('+ps+')'
    def fi(i):
        o=field_off+8*i; return ts(u2(data,o)), gs(u4(data,o+4))

    for ci in range(cds):
        co=cdo+32*ci
        cd=ts(u4(data,co))
        if cd != cls: continue
        cdatao=u4(data,co+24)
        if cdatao==0: return None
        p=cdatao
        def ub():
            nonlocal p
            r=0;s=0
            while True:
                b=data[p]; r|=(b&0x7f)<<s; s+=7; p+=1
                if not (b&0x80): break
            return r
        sf=ub(); iff=ub(); dm=ub(); vm=ub()
        for _ in range(sf): ub(); ub()
        for _ in range(iff): ub(); ub()
        for kind,cnt in (('D',dm),('V',vm)):
            midx=0
            for _ in range(cnt):
                diff=ub(); _a=ub(); co2=ub(); midx+=diff
                if co2==0: continue
                mc,mn,md=mi(midx)
                if mn!=meth: continue
                ins_n=u2(data,co2+2); outs_n=u2(data,co2+4)
                insns_n=u4(data,co2+12); io=co2+16
                print(f'== {cd} -> {mn}{md} regs/ins/outs in header: ins={ins_n} outs={outs_n} units={insns_n}')
                pc=0
                while pc<insns_n:
                    u=u2(data,io+2*pc); op=u&0xff
                    def A(): return (u>>8)&0xf
                    def AA(): return (u>>8)&0xff
                    def B(): return u2(data,io+2*(pc+1))
                    def BBBB(): return (u2(data,io+2*(pc+2))<<16)|0  # placeholder
                    name=f'op{op:#04x}'
                    det=''
                    if op in (0x52,0x53,0x54,0x55,0x56,0x57,0x58):
                        fc,fn=fi(B()); name='iget-family'; det=f'v{A()}, v{(u>>12)&0xf}, {fc}.{fn}'
                    elif op in (0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f):
                        fc,fn=fi(B()); name='iput-family'; det=f'v{A()}, v{(u>>12)&0xf}, {fc}.{fn}'
                    elif op in (0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d):
                        fc,fn=fi(B()); name='sget/sput'; det=f'v{A()}, {fc}.{fn}'
                    elif op in (0x6e,0x6f,0x70,0x71,0x72):
                        mc2,mn2,md2=mi(B()); G=(u>>12)&0xf; Aa=A()
                        name={0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface'}[op]
                        regs=[(G>>0)&0xf,(G>>4)&0xf,(u>>20)&0xf if False else 0,0,0]
                        det=f'{mn2}{md2} [A={Aa} F={G&0xf} E={(G>>4)&0xf}]'
                    elif op in (0x74,0x75,0x76,0x77,0x78):
                        mc2,mn2,md2=mi(B()); AA_=AA()
                        name={0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',0x77:'invoke-static/range',0x78:'invoke-interface/range'}[op]
                        det=f'{mn2}{md2} v{AA_}..'
                    elif op==0x22:
                        name='new-instance'; det=f'v{A()}, type@{B()} -> {ts(B())}'
                    elif op==0x1f:
                        name='check-cast'; det=f'v{A()}, {ts(B())}'
                    elif op==0x20:
                        name='instance-of'; det=f'v{A()}, v{(u>>12)&0xf}, {ts(B())}'
                    elif op==0x0a: name='move-result'; det=f'v{AA()}'
                    elif op==0x0b: name='move-result-wide'; det=f'v{AA()}'
                    elif op==0x0c: name='move-result-object'; det=f'v{AA()}'
                    elif op==0x01: name='move'; det=f'v{A()}, v{(u>>12)&0xf}'
                    elif op==0x07: name='move-object'; det=f'v{A()}, v{(u>>12)&0xf}'
                    elif op==0x08: name='move-object/from16'; det=f'v{A()}, v{u2(data,io+2*(pc+1))&0xff}'
                    elif op==0x12: name='const/4'; det=f'v{A()}, {(u>>12)&0xf if ((u>>12)&0xf)<8 else ((u>>12)&0xf)-16}'
                    elif op==0x13: name='const/16'; det=f'v{A()}, {struct.unpack_from("<h",data,io+2*(pc+1))[0]}'
                    elif op==0x14: name='const'; det=f'v{A()}, {struct.unpack_from("<i",data,io+2*(pc+1))[0]}'
                    elif op==0x15: name='const/high16'; det=f'v{A()}, {(u2(data,io+2*(pc+1))<<16):#x}'
                    elif op==0x28: name='goto'; det=f'{((u>>8)&0xff)-256 if (u>>8)&0x80 else (u>>8)&0xff}'
                    elif op==0x29:
                        o2=struct.unpack_from('<h',data,io+2*(pc+1))[0]; name='goto/16'; det=f'{o2}'
                    elif op==0x2b: name='packed-switch'; det=f'v{AA()}, @{pc*2+struct.unpack_from("<i",data,io+2*(pc+1))[0]*2}'
                    elif op==0x2c: name='sparse-switch'; det=f'v{AA()}, @{pc*2+struct.unpack_from("<i",data,io+2*(pc+1))[0]*2}'
                    elif op==0x26: name='fill-array-data'; det=f'v{AA()}, @{pc*2+struct.unpack_from("<i",data,io+2*(pc+1))[0]*2}'
                    elif 0x32<=op<=0x37:
                        nm={0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',0x37:'if-le'}[op]
                        o2=struct.unpack_from('<h',data,io+2*(pc+1))[0]
                        name=nm; det=f'v{A()}, v{(u>>12)&0xf}, -> {pc*2+o2*2:#x}'
                    elif 0x38<=op<=0x3d:
                        nm={0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez'}[op]
                        o2=struct.unpack_from('<h',data,io+2*(pc+1))[0]
                        name=nm; det=f'v{A()}, -> {pc*2+o2*2:#x}'
                    elif 0x2d<=op<=0x31:
                        name='cmpl/cmpg'; det=f'v{AA()}, v{A()}, v{(u>>12)&0xf}'
                    elif 0x44<=op<=0x51:
                        name='aget/aput'; det=f'v{A()}, v{(u>>12)&0xf}, v{B()&0xff}'
                    elif 0x90<=op<=0xaf:
                        name='binop'; det=f'v{AA()}, v{A()}, v{(u>>12)&0xf}'
                    elif 0xb0<=op<=0xcf:
                        name='binop/2addr'; det=f'v{A()}, v{(u>>12)&0xf}'
                    elif 0xd0<=op<=0xd7:
                        name='binop/lit16'; det=f'v{AA()}, v{A()}, lit'
                    elif 0xd8<=op<=0xe2:
                        name='binop/lit8'; det=f'v{AA()}, v{A()}, lit'
                    elif op==0x11: name='return-wide'; det=f'v{AA()}'
                    elif op==0x0f: name='return'; det=f'v{AA()}'
                    elif op==0x10: name='return-wide'; det=f'v{AA()}'
                    elif op==0x11: name='return-wide'; det=f'v{AA()}'
                    elif op==0x0e: name='return-void'
                    elif op==0x00:
                        hi=u>>8
                        name='nop' if hi==0 else f'payload-{hi:#04x}'
                    elif op==0x21: name='array-length'; det=f'v{A()}, v{(u>>12)&0xf}'
                    elif op==0x23: name='new-array'; det=f'v{A()}, v{(u>>12)&0xf}, {ts(B())}'
                    elif op==0x24: name='filled-new-array'; det=f'type@{B()}'
                    elif op==0x27: name='throw'; det=f'v{AA()}'
                    elif op==0x1a: name='const-string'; det=f'v{A()}, "{gs(B())[:60]}"'
                    elif op==0x1b: name='const-string/jumbo'; det=f'v{AA()}, "{gs(u4(data,io+2*(pc+1)))[:60]}"'
                    elif op==0x1c: name='const-class'; det=f'v{A()}, {ts(B())}'
                    elif op==0x1d: name='monitor-enter'; det=f'v{AA()}'
                    elif op==0x1e: name='monitor-exit'; det=f'v{AA()}'
                    # size in units
                    sz=1
                    if op in (0x02,0x05,0x08,0x09,0x13,0x15,0x16,0x19,0x1a,0x1c,0x1f,0x20,0x22,0x23): sz=2
                    elif op in (0x03,0x06,0x09,0x14,0x17,0x1b,0x24,0x25,0x26,0x2a,0x2b,0x2c) or 0x2d<=op<=0x3d or 0x44<=op<=0x6d or 0x90<=op<=0xaf or (0xd0<=op<=0xe2): sz=2
                    elif op in (0x18,): sz=5
                    elif op in (0x24,0x25,0x26): sz=3
                    elif 0x6e<=op<=0x72 or 0x74<=op<=0x78: sz=3
                    print(f'  {pc*2:#06x}: {name:22s} {det}')
                    if op==0x00:
                        hi=u>>8
                        if hi==0x01:
                            ew=u2(data,io+2*(pc+1)); n_=u4(data,io+2*(pc+2))
                            pc+=(8+n_*ew+1)//2; continue
                        if hi==0x02:
                            n_=u2(data,io+2*(pc+1)); pc+=2+4*n_; continue
                        if hi==0x03:
                            n_=u2(data,io+2*(pc+1)); pc+=4+2*n_; continue
                    pc+=sz
                return 'done'
    return None

for dn in sorted(n for n in zf.namelist() if n.startswith('classes') and n.endswith('.dex')):
    r=run(dn, zf.read(dn))
    if r: break
