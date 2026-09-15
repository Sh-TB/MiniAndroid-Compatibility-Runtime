#!/usr/bin/env python3
"""GPG probe: exact register encoding of z1/i.addAll's Intrinsics call."""
import struct, zipfile, sys

apk = 'miniandroid/download/exp076_corpus/io.github.yamin8000.dooz_18.apk'
z2 = zipfile.ZipFile(apk)
d = z2.read('classes.dex')

def u4(o): return struct.unpack_from('<I', d, o)[0]
def u2(o): return struct.unpack_from('<H', d, o)[0]
def uleb(p):
    r=0;s=0
    while True:
        b=d[p+s]; r|=(b&0x7f)<<(7*s); s+=1
        if not (b&0x80): return r,p+s

s_sz,s_off=u4(0x38),u4(0x3c); t_sz,t_off=u4(0x40),u4(0x44)
p_sz,p_off=u4(0x48),u4(0x4c)
m_sz,m_off=u4(0x58),u4(0x5c); c_sz,c_off=u4(0x60),u4(0x64)
strs=[]
for i in range(s_sz):
    off=u4(s_off+4*i); n,p2=uleb(off); strs.append(d[p2:p2+n].decode('utf-8','replace'))
def type_desc(i):
    if i>=t_sz: return '?'
    return strs[u4(t_off+4*i)]
def proto(i):
    base=p_off+12*i
    shorty=strs[u4(base)]; ret=type_desc(u4(base+4)); poff=u4(base+8); params=[]
    if poff:
        n=u4(poff)
        for k in range(n): params.append(type_desc(u2(poff+4+2*k)))
    return shorty,ret,params
def method_ref(i):
    if i>=m_sz: raise IndexError()
    base=m_off+8*i
    return type_desc(u2(base)), strs[u4(base+4)], proto(u2(base+2))
class_defs=[]
for i in range(c_sz):
    base=c_off+32*i
    class_defs.append({'name':type_desc(u4(base)),'cdo':u4(base+24)})
def methods_of(cdo):
    if not cdo: return []
    p=cdo
    sf,p=uleb(p); inf,p=uleb(p); sm,p=uleb(p); vm,p=uleb(p)
    idx=0
    for k in range(sf): d1,p=uleb(p); d2,p=uleb(p); idx+=d1
    idx=0
    for k in range(inf): d1,p=uleb(p); d2,p=uleb(p); idx+=d1
    out=[]; idx=0
    for k in range(sm): d1,p=uleb(p); acc,p=uleb(p); co,p=uleb(p); idx+=d1; out.append((idx,co,'D'))
    idx=0
    for k in range(vm): d1,p=uleb(p); acc,p=uleb(p); co,p=uleb(p); idx+=d1; out.append((idx,co,'V'))
    return out

for cd in class_defs:
    if cd['name']!='Lz1/i;': continue
    for midx,co,dk in methods_of(cd['cdo']):
        try: c2,n2,(ret,par)=method_ref(midx)
        except Exception: continue
        if n2!='addAll': continue
        print('z1/i.addAll', par,'->',ret,'code',hex(co))
        isz=u4(co+12); io=co+16
        for u in range(0,6):
            w=u2(io+2*u)
            print('  unit %d: 0x%04x' % (u,w))
        w=u2(io+2*2)
        A=(w>>12)&0xF; G=(w>>8)&0xF
        midx2=u2(io+2*3); rw=u2(io+2*4)
        mc,mn,(sh,rt,pp)=method_ref(midx2)
        regs=[rw&0xF,(rw>>4)&0xF,(rw>>8)&0xF,(rw>>12)&0xF,G]
        print('  invoke-static %s.%s shorty=%s params=%s argc=%d CDEFG=%s' % (mc,mn,sh,pp,A,regs))
        regs_size=u2(co); ins=u2(co+2); outs=u2(co+4)
        print('  frame: registers_size=%d ins=%d outs=%d' % (regs_size,ins,outs))
