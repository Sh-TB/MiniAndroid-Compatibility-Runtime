#!/usr/bin/env python3
"""cont28_disasm.py — minimal CORRECT dalvik disassembler (width-table based).
usage: cont28_disasm.py <apk> <class-descriptor> [method-substring]
"""
import struct, sys, zipfile

def uleb128(buf, off):
    r = 0; sh = 0
    while True:
        b = buf[off]; off += 1
        r |= (b & 0x7f) << sh
        if not (b & 0x80): break
        sh += 7
    return r, off

# widths in 16-bit code units for opcodes 0x00-0xff (payload nops handled too)
W = [1]*256
for op in range(0x01, 0x0c): W[op] = 1          # moves
W[0x0c]=1; W[0x0d]=1; W[0x0e]=1; W[0x0f]=1; W[0x10]=1; W[0x11]=1
W[0x12]=1                                        # const/4
W[0x13]=2; W[0x14]=3; W[0x15]=2                  # const/16, const, const/high16
W[0x16]=2; W[0x17]=3; W[0x18]=5; W[0x19]=2       # const-wide family
W[0x1a]=2; W[0x1b]=3                             # const-string, jumbo
W[0x1c]=2; W[0x1d]=1; W[0x1e]=1; W[0x1f]=2; W[0x20]=2
W[0x21]=1; W[0x22]=2; W[0x23]=2; W[0x24]=3; W[0x25]=3; W[0x26]=3
W[0x27]=1; W[0x28]=1; W[0x29]=2; W[0x2a]=3; W[0x2b]=3; W[0x2c]=3
for op in range(0x2d, 0x32): W[op]=2             # cmp
for op in range(0x32, 0x38): W[op]=2             # if-test
for op in range(0x38, 0x3e): W[op]=2             # if-testz
for op in range(0x44, 0x52): W[op]=2             # aget/aput
for op in range(0x52, 0x60): W[op]=2             # iget/iput
for op in range(0x60, 0x6e): W[op]=2             # sget/sput
for op in range(0x6e, 0x73): W[op]=3             # invoke-kind
W[0x73]=1
for op in range(0x74, 0x79): W[op]=3             # invoke-kind/range
W[0x79]=1; W[0x7a]=1
for op in range(0x7b, 0x90): W[op]=1             # unop
for op in range(0x90, 0xb0): W[op]=2             # binop
for op in range(0xb0, 0xd0): W[op]=1             # binop/2addr
for op in range(0xd0, 0xd8): W[op]=2             # binop/lit16
for op in range(0xd8, 0xe3): W[op]=2             # binop/lit8

NAMES = {0x22:"new-instance",0x23:"new-array",0x1c:"const-class",0x1f:"check-cast",
         0x20:"instance-of",0x70:"invoke-direct",0x71:"invoke-virtual",0x72:"invoke-super",
         0x73:"unused",0x74:"invoke-virtual/range",0x75:"invoke-super/range",
         0x76:"invoke-direct/range",0x77:"invoke-static/range",0x78:"invoke-interface/range",
         0x6e:"invoke-virtual",0x6f:"invoke-super"}
NAMES[0x6e]="invoke-virtual"; NAMES[0x6f]="invoke-super"; NAMES[0x70]="invoke-direct"
NAMES[0x71]="invoke-virtual"; NAMES[0x72]="invoke-super"; NAMES[0x6c]="sget"
NAMES[0x77]="invoke-static/range"; NAMES[0x71]="invoke-virtual"
for i,base in enumerate(["invoke-virtual","invoke-super","invoke-direct","invoke-static","invoke-interface"]):
    NAMES[0x6e+i]=base
for i,base in enumerate(["invoke-virtual/range","invoke-super/range","invoke-direct/range","invoke-static/range","invoke-interface/range"]):
    NAMES[0x74+i]=base
for i,base in enumerate(["iget","iget-wide","iget-object","iget-boolean","iget-byte","iget-char","iget-short",
                          "iput","iput-wide","iput-object","iput-boolean","iput-byte","iput-char","iput-short"]):
    NAMES[0x52+i]=base
for i,base in enumerate(["sget","sget-wide","sget-object","sget-boolean","sget-byte","sget-char","sget-short",
                          "sput","sput-wide","sput-object","sput-boolean","sput-byte","sput-char","sput-short"]):
    NAMES[0x60+i]=base
for i,b in enumerate(["aget","aget-wide","aget-object","aget-boolean","aget-byte","aget-char","aget-short",
                       "aput","aput-wide","aput-object","aput-boolean","aput-byte","aput-char","aput-short"]):
    NAMES[0x44+i]=b
NAMES[0x0a]="move-result"; NAMES[0x0b]="move-result-wide"; NAMES[0x0c]="move-result-object"
NAMES[0x0d]="move-exception"; NAMES[0x0e]="return-void"; NAMES[0x0f]="return"
NAMES[0x10]="return-wide"; NAMES[0x11]="return-object"; NAMES[0x12]="const/4"
NAMES[0x13]="const/16"; NAMES[0x14]="const"; NAMES[0x15]="const/high16"
NAMES[0x1a]="const-string"; NAMES[0x27]="throw"; NAMES[0x28]="goto"
NAMES[0x29]="goto/16"; NAMES[0x2a]="goto/32"; NAMES[0x21]="array-length"

class Dex:
    def __init__(self, name, d):
        self.name=name; self.d=d
        g=lambda o: struct.unpack_from("<I", d, o)[0]
        self.string_ids_off=g(0x3c)
        self.type_ids_off=g(0x44)
        self.proto_ids_off=g(0x4c)
        self.field_ids_off=g(0x54)
        self.method_ids_off=g(0x5c)
        self.class_defs_off=g(0x64)
        self.class_defs_size=g(0x60)
    def s(self, idx):
        off=struct.unpack_from("<I",self.d,self.string_ids_off+4*idx)[0]
        n,o=uleb128(self.d,off)
        end=self.d.index(b"\x00",o)
        return self.d[o:end].decode("utf-8","replace")
    def t(self, idx): return self.s(struct.unpack_from("<I",self.d,self.type_ids_off+4*idx)[0])
    def f(self, idx):
        ci=struct.unpack_from("<H",self.d,self.field_ids_off+8*idx)[0]
        si=struct.unpack_from("<H",self.d,self.field_ids_off+8*idx+2)[0]
        return f"{self.t(ci)}.{self.s(si)}"
    def m(self, idx):
        b=self.method_ids_off+8*idx
        ci=struct.unpack_from("<H",self.d,b)[0]
        pi=struct.unpack_from("<H",self.d,b+2)[0]
        si=struct.unpack_from("<I",self.d,b+4)[0]
        po=struct.unpack_from("<I",self.d,self.proto_ids_off+12*pi+8)[0]
        ret=self.t(struct.unpack_from("<H",self.d,self.proto_ids_off+12*pi+4)[0])
        ps=""
        if po:
            n,o=uleb128(self.d,po)
            ps="".join(self.t(struct.unpack_from("<H",self.d,po+4+2*i)[0]) for i in range(n))
        return f"{self.t(ci)}.{self.s(si)}({ps}){ret}"
    def classes(self):
        for i in range(self.class_defs_size):
            ci=struct.unpack_from("<I",self.d,self.class_defs_off+32*i)[0]
            yield self.t(ci), self.class_defs_off+32*i
    def method_code(self, cd_off):
        d=self.d
        cdo=struct.unpack_from("<I",d,cd_off+24)[0]
        if not cdo: return
        off=cdo
        sf,off=uleb128(d,off); inf,off=uleb128(d,off)
        dm,off=uleb128(d,off); vm,off=uleb128(d,off)
        fidx=0
        for _ in range(sf):
            di,off=uleb128(d,off); fidx+=di; _,off=uleb128(d,off)
        for _ in range(inf):
            di,off=uleb128(d,off); fidx+=di; _,off=uleb128(d,off)
        midx=0
        for _ in range(dm):
            di,off=uleb128(d,off); midx+=di
            _,off=uleb128(d,off); co,off=uleb128(d,off)
            yield self.m(midx), co
        midx=0
        for _ in range(vm):
            di,off=uleb128(d,off); midx+=di
            _,off=uleb128(d,off); co,off=uleb128(d,off)
            yield self.m(midx), co

def code_item(d, co):
    if co==0: return None
    regs,ins,outs,tries,dbg,size=struct.unpack_from("<HHHHII",d,co)
    if size==0: return None
    return dict(regs=regs,ins=ins,outs=outs,off=co+16,size=size,tries=tries,
                tries_off=co+16+size*2+ (0 if (size%2)==0 else 2))

def dump(dx, cls, want):
    for c, cd in dx.classes():
        if c != cls: continue
        for msig, co in dx.method_code(cd):
            ci = dx.s if False else None
            mname = msig.split(';.')[1].split('(')[0] if ';.' in msig else msig
            if want and want not in msig: continue
            code = code_item(dx.d, co)
            if not code:
                print(f"{msig}  <no code>"); continue
            print(f"{msig}  regs={code['regs']} ins={code['ins']} size={code['size']}")
            d=dx.d; off=code['off']; end=off+code['size']*2
            while off<end:
                pc=(off-code['off'])//2
                op=d[off]
                w=W[op]
                txt=""
                if op==0x22 or op==0x1c or op==0x1f or op==0x20:
                    ti=struct.unpack_from("<H",d,off+2)[0]
                    txt=f"v{d[off+1]} {dx.t(ti)}"
                elif op in (0x23,):
                    ti=struct.unpack_from("<H",d,off+2)[0]
                    txt=f"v{d[off+1]} {dx.t(ti)}"
                elif 0x6e<=op<=0x72 or 0x74<=op<=0x78:
                    mi=struct.unpack_from("<H",d,off+2)[0]
                    txt=dx.m(mi)
                elif 0x52<=op<=0x5f:
                    fi=struct.unpack_from("<H",d,off+2)[0]
                    txt=f"v{d[off+1]} v{d[off+4] if False else ''} {dx.f(fi)}"
                    regs=struct.unpack_from("<BB",d,off+1)
                    txt=f"v{regs[0]} v{regs[1]} {dx.f(fi)}"
                elif 0x60<=op<=0x6d:
                    fi=struct.unpack_from("<H",d,off+2)[0]
                    txt=f"v{d[off+1]} {dx.f(fi)}"
                elif op==0x1a:
                    si=struct.unpack_from("<H",d,off+2)[0]
                    txt=f"v{d[off+1]} \"{dx.s(si)[:60]}\""
                elif op in (0x0f,0x10,0x11,0x0a,0x0b,0x0c,0x0d):
                    txt=f"v{d[off+1]}"
                elif op==0x12:
                    b=d[off+1]; txt=f"v{b&0xf} #{(b>>4)&0xf if (b>>4)<8 else (b>>4)-16}"
                elif 0x32<=op<=0x37:
                    aa=d[off+1]; bb=d[off+2]
                    tgt=struct.unpack_from("<h",d,off+2)[0] if False else 0
                    txt=f"v{aa}, v{bb}, +{struct.unpack_from('<h',d,off+2)[0] if False else ''}"
                    txt=f"v{aa}, v{d[off+2]}, {pc+struct.unpack_from('<h',d,off+4)[0] if False else 0}"
                    # format 22t: A|B in byte2, CCCC at +2? actually 22t: op, A|B, CCCC
                    tgt=pc+struct.unpack_from("<h",d,off+2)[0]
                    regs=struct.unpack_from("<BB",d,off+1)
                    txt=f"v{regs[0]&0xf}, v{regs[0]>>4}, ->{pc+tgt}"
                print(f"  @{pc:#06x} {NAMES.get(op,f'op-{op:#04x}'):24s} {txt}")
                off+=w*2
            print()

def main():
    apk, cls = sys.argv[1], sys.argv[2]
    want = sys.argv[3] if len(sys.argv)>3 else None
    z=zipfile.ZipFile(apk)
    for n in z.namelist():
        if not n.endswith(".dex"): continue
        dump(Dex(n, z.read(n)), cls, want)

if __name__=="__main__":
    main()
