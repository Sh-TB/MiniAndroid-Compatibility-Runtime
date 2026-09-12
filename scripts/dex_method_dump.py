#!/usr/bin/env python3
"""Dump Dalvik bytecode of a method from any APK (all classes*.dex).

Usage: dex_method_dump.py <apk> <class-descriptor> <method-name|-all>
Example: dex_method_dump.py app.apk Lomegacentauri/mobi/simplestopwatch/MyStateDrawable; draw
"""
import zipfile, struct, sys

# Dalvik opcode formats (subset covering common ops; names for display only)
FMT = {}
def _op(code, name, fmt):
    FMT[code] = (name, fmt)
for c, n, f in [
    (0x00,'nop','10x'),(0x01,'move','12x'),(0x02,'move/from16','22x'),(0x03,'move/16','32x'),
    (0x04,'move-wide','12x'),(0x05,'move-wide/from16','22x'),(0x07,'move-object','12x'),
    (0x08,'move-object/from16','22x'),(0x0a,'move-result','11x'),(0x0b,'move-result-wide','11x'),
    (0x0c,'move-result-object','11x'),(0x0d,'move-exception','11x'),(0x0e,'return-void','10x'),
    (0x0f,'return','11x'),(0x10,'return-wide','11x'),(0x11,'return-object','11x'),
    (0x12,'const/4','11n'),(0x13,'const/16','21s'),(0x14,'const','31i'),(0x15,'const/high16','21h'),
    (0x16,'const-wide/16','21s'),(0x17,'const-wide/32','31i'),(0x18,'const-wide','51l'),
    (0x19,'const-wide/high16','21h'),(0x1a,'const-string','21c'),(0x1b,'const-string/jumbo','31c'),
    (0x1c,'const-class','21c'),(0x1d,'monitor-enter','11x'),(0x1e,'monitor-exit','11x'),
    (0x1f,'check-cast','21c'),(0x20,'instance-of','22c'),(0x21,'array-length','12x'),
    (0x22,'new-instance','21c'),(0x23,'new-array','22c'),(0x24,'filled-new-array','35c'),
    (0x25,'filled-new-array/range','3rc'),(0x26,'fill-array-data','31t'),(0x27,'throw','11x'),
    (0x28,'goto','10t'),(0x29,'goto/16','20t'),(0x2a,'goto/32','30t'),(0x2b,'packed-switch','31t'),
    (0x2c,'sparse-switch','31t'),(0x2d,'cmpl-float','23x'),(0x2e,'cmpg-float','23x'),
    (0x2f,'cmpl-double','23x'),(0x30,'cmpg-double','23x'),(0x31,'cmp-long','23x'),
    (0x32,'if-eq','22t'),(0x33,'if-ne','22t'),(0x34,'if-lt','22t'),(0x35,'if-ge','22t'),
    (0x36,'if-gt','22t'),(0x37,'if-le','22t'),(0x38,'if-eqz','21t'),(0x39,'if-nez','21t'),
    (0x3a,'if-ltz','21t'),(0x3b,'if-gez','21t'),(0x3c,'if-gtz','21t'),(0x3d,'if-lez','21t'),
    (0x44,'aget','23x'),(0x4b,'aput','23x'),(0x4f,'iput','22c'),(0x50,'iput-wide','22c'),
    (0x52,'iget','22c'),(0x53,'iget-wide','22c'),(0x54,'iget-object','22c'),(0x55,'iget-boolean','22c'),
    (0x59,'iput','22c'),(0x5a,'iput-wide','22c'),(0x5b,'iput-object','22c'),
    (0x60,'sget','21c'),(0x61,'sget-wide','21c'),(0x62,'sget-object','21c'),(0x63,'sget-boolean','21c'),(0x69,'sput','21c'),
    (0x6e,'invoke-virtual','35c'),(0x6f,'invoke-super','35c'),(0x70,'invoke-direct','35c'),
    (0x71,'invoke-static','35c'),(0x72,'invoke-interface','35c'),
    (0x74,'invoke-virtual/range','3rc'),(0x76,'invoke-direct/range','3rc'),
    (0x77,'invoke-static/range','3rc'),(0x78,'invoke-interface/range','3rc'),
    (0x7b,'neg-int','12x'),(0x7d,'not-int','12x'),(0x7e,'neg-long','12x'),
    (0x81,'long-to-int','12x'),(0x83,'int-to-long','12x'),(0x84,'int-to-float','12x'),
    (0x85,'int-to-double','12x'),(0x86,'long-to-float','12x'),(0x87,'long-to-double','12x'),
    (0x88,'float-to-int','12x'),(0x89,'float-to-long','12x'),(0x8a,'float-to-double','12x'),
    (0x8b,'double-to-int','12x'),(0x8c,'double-to-long','12x'),(0x8d,'double-to-float','12x'),
    (0x8f,'int-to-byte','12x'),(0x90,'int-to-char','12x'),(0x91,'int-to-short','12x'),
    (0x90,'int-to-char','12x'),
    (0x92,'add-int','23x'),(0x93,'sub-int','23x'),(0x94,'mul-int','23x'),(0x95,'div-int','23x'),
    (0x9b,'add-long','23x'),(0x9d,'mul-long','23x'),(0xa0,'add-float','23x'),(0xa2,'add-double','23x'),
    (0xb0,'add-int/2addr','12x'),(0xb1,'sub-int/2addr','12x'),(0xb2,'mul-int/2addr','12x'),
    (0xb3,'div-int/2addr','12x'),(0xb6,'add-long/2addr','12x'),(0xbb,'add-float/2addr','12x'),
    (0xbd,'add-double/2addr','12x'),(0xbf,'sub-float/2addr','12x'),
    (0xd0,'add-int/lit16','22s'),(0xd2,'mul-int/lit16','22s'),(0xd5,'and-int/lit16','22s'),
    (0xd8,'add-int/lit8','22b'),(0xd9,'rsub-int/lit8','22b'),(0xda,'mul-int/lit8','22b'),
    (0xdb,'div-int/lit8','22b'),(0xdc,'rem-int/lit8','22b'),(0xdd,'and-int/lit8','22b'),
    (0xde,'or-int/lit8','22b'),(0xdf,'xor-int/lit8','22b'),(0xe0,'shl-int/lit8','22b'),
    (0xe1,'shr-int/lit8','22b'),(0xe2,'ushr-int/lit8','22b'),
    (0xc8,'neg-double','12x'),(0xca,'int-to-short','12x'),
    (0xa3,'add-double/2addr','12x'),
    (0xbf,'sub-float/2addr','12x'),
    (0xc0,'sub-double/2addr','12x'),
    (0xa1,'sub-float','23x'),
    (0xa7,'cmpg-float','23x'),
]:
    _op(c, n, f)

def u4(d,o): return struct.unpack_from('<I', d, o)[0]
def u2(d,o): return struct.unpack_from('<H', d, o)[0]

def uleb(d,p):
    r=0; s=0
    while True:
        b=d[p]; p+=1
        r |= (b&0x7f)<<s; s+=7
        if not (b&0x80): break
    return r,p

def sleb(d,p):
    r=0; s=0
    while True:
        b=d[p]; p+=1
        r |= (b&0x7f)<<s; s+=7
        if not (b&0x80):
            if b & 0x40: r -= (1<<s)
            break
    return r,p

class Dex:
    def __init__(self, data):
        self.d = data
        self.str_off = u4(data,0x3c); self.typ_off = u4(data,0x44)
        self.pro_off = u4(data,0x4c)
        self.fld_off = u4(data,0x54); self.mtd_off = u4(data,0x5c)
        self.cls_off = u4(data,0x64)
        self.n_str = u4(data,0x38); self.n_typ = u4(data,0x40)
        self.n_mtd = u4(data,0x58); self.n_cls = u4(data,0x60)
    def s(self,i):
        off = u4(self.d, self.str_off + i*4)
        p = off
        _n,p = uleb(self.d,p)
        e = self.d.index(b'\x00', p)
        return self.d[p:e].decode('utf-8','replace')
    def t(self,i): return self.s(u4(self.d, self.typ_off + i*4))
    def field(self,i):
        o = self.fld_off + i*8
        cls = self.t(u2(self.d,o)); typ = self.t(u2(self.d,o+2)); nm = self.s(u4(self.d,o+4))
        return f"{cls}.{nm}:{typ}"
    def method(self,i):
        o = self.mtd_off + i*8
        cls = self.t(u2(self.d,o)); nm = self.s(u4(self.d,o+4))
        po = self.pro_off + u2(self.d,o+2)*12
        ret = self.t(u4(self.d,po+4))
        poff = u4(self.d,po+8)
        params = []
        if poff:
            n = u4(self.d,poff)
            params = [self.t(u2(self.d,poff+4+k*2)) for k in range(n)]
        return f"{cls}.{nm}({','.join(params)}){ret}"
    def classes(self):
        for c in range(self.n_cls):
            yield self.cls_off + c*32
    def find_class(self, desc):
        for o in self.classes():
            if self.t(u2(self.d,o)) == desc:
                return o
        return None
    def methods_of(self, o):
        cdo = u4(self.d,o+24)
        if cdo == 0: return []
        p = cdo
        sf,p = uleb(self.d,p); inf,p = uleb(self.d,p); dm,p = uleb(self.d,p); vm,p = uleb(self.d,p)
        out = []
        for _ in range(sf + inf):
            _,p = uleb(self.d,p); _,p = uleb(self.d,p)
        vi = 0
        for _ in range(dm):
            diff,p = uleb(self.d,p)
            _,p = uleb(self.d,p)
            code,p = uleb(self.d,p)
            vi += diff
            mo = self.mtd_off + vi*8
            out.append((self.s(u4(self.d,mo+4)), code))  # name, code_off (uleb from class_data)
        vi = 0  # virtual list restarts its index accumulation (Dex spec)
        for _ in range(vm):
            diff,p = uleb(self.d,p)
            _,p = uleb(self.d,p)
            code,p = uleb(self.d,p)
            vi += diff
            mo = self.mtd_off + vi*8
            out.append((self.s(u4(self.d,mo+4)), code))
        return out

SIZE = {'10x':1,'10t':1,'11x':1,'11n':1,'12x':1,'20t':2,'21s':2,'21h':2,'21c':2,'22x':2,
        '21i':3,'22b':2,'22s':2,'22c':2,'22t':2,'23x':2,'30t':3,'31t':3,'31i':3,'31c':3,
        '32x':3,'35c':3,'3rc':3,'51l':5}

def disasm(dex, code_off, out):
    d = dex.d
    insns_size = u4(d, code_off+12)
    insns = code_off+16
    p = insns; end = insns + insns_size*2
    # build map: method idx @ index -> label for later resolution
    idx = 0
    insts = []
    while p < end:
        op = d[p]
        name, fmt = FMT.get(op, (f'op-{op:#04x}','10x'))
        sz = SIZE.get(fmt,1)
        raw = d[p:p+sz*2]
        b1 = d[p+1]
        note = ''
        if fmt == '21c' and op in (0x1a,0x1b):
            sidx = u2(d,p+2) if op==0x1a else u4(d,p+2)
            note = f' "{dex.s(sidx)}"'
        elif fmt in ('21c','22c','31c') and op in (0x1c,0x1f,0x22,0x23):
            note = f' {dex.t(u2(d,p+2))}'
        elif fmt in ('21c',) and op in (0x60,0x62,0x63,0x69):
            note = f' {dex.field(u2(d,p+2))}'
        elif fmt in ('22c',) and op in (0x4f,0x50,0x54,0x59,0x5a,0x5e):
            note = f' {dex.field(u2(d,p+2))}'
        elif fmt in ('35c','3rc'):
            m = u2(d,p+2) if fmt=='35c' else u2(d,p+2)
            note = f' {dex.method(m)}'
        elif fmt == '31i':
            note = f' #0x{u4(d,p+2):08x}'
        elif fmt == '21s':
            note = f' #0x{u2(d,p+2):04x}'
        elif fmt == '21h':
            note = f' #0x{u2(d,p+2):04x}<<{(0,16,32,48)[(op-0x15)] if 0x15<=op<=0x19 else 0}'
        elif fmt == '11n':
            note = f' #0x{(b1>>4)&0xf:01x}'
        elif fmt == '51l':
            note = f' #0x{struct.unpack_from("<Q",d,p+2)[0]:016x}'
        insts.append((idx, f'{p:#08x}: {name}{note}'))
        p += sz*2
        idx += sz
    for i,line in insts:
        print(line)

def main():
    apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
    z = zipfile.ZipFile(apk)
    for name in z.namelist():
        if name.startswith('classes') and name.endswith('.dex'):
            dex = Dex(z.read(name))
            o = dex.find_class(cls)
            if o is None: continue
            print(f'# {name} class {cls}')
            for mname, code_off in dex.methods_of(o):
                if meth in ('-all', mname):
                    print(f'### {cls}.{mname} (code_off={code_off:#x})')
                    if code_off:
                        disasm(dex, code_off, sys.stdout)
                    print()

if __name__ == '__main__':
    main()
