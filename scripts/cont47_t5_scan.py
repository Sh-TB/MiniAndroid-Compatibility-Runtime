#!/usr/bin/env python3
"""CONT-47 T5 part 2: full config-chain census over MessagesController.
For every MC method body: find new-instance of TL_* request classes +
sendRequest*/ConnectionsManager dispatch + the RequestDelegate lambda class
passed. Then for each lambda class dump its run(TLObject,TL_error) instanceof
checks + response field reads. Also dump the ka; RequestDelegate family."""
import sys, zipfile, struct, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

APK = os.environ.get('MA_DEX_APK', '/home/z/my-project/upload/telegram_official.apk')
MC = 'Lorg/telegram/messenger/MessagesController;'

z = zipfile.ZipFile(APK)
ALL_DEXES = [(n, z.read(n)) for n in z.namelist() if n.endswith('.dex')]

OPS = {0x00:'nop',0x0e:'return-void',0x0f:'return',0x11:'return-object',
       0x12:'const/4',0x1a:'const-string',0x1c:'const-class',0x1f:'check-cast',
       0x20:'instance-of',0x22:'new-instance',0x54:'iget-object',0x52:'iget',
       0x55:'iget-boolean',0x5b:'iput-object',0x62:'sget-object',
       0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
       0x71:'invoke-static',0x72:'invoke-interface',0x38:'if-eqz',0x39:'if-nez',
       0x74:'invoke-virtual/range',0x77:'invoke-static/range'}
W1 = {0x0e,0x0f,0x11,0x12,0x27,0x28,0x1d,0x1e,0x21} | set(range(0x7b,0xb0))
W2 = {0x13,0x15,0x16,0x19,0x1a,0x1c,0x1f,0x20,0x22,0x23} | set(range(0x29,0x2d)) | set(range(0x32,0x3e)) | set(range(0x44,0x6e)) | set(range(0xd0,0xe3))
W3 = set(range(0x6e,0x73)) | set(range(0x74,0x79)) | {0x14,0x17,0x18,0x1b,0x24,0x25,0x26,0x2a,0x2b,0x2c}
def u2(b,o): return struct.unpack_from('<H',b,o)[0]
def u4(b,o): return struct.unpack_from('<I',b,o)[0]

class Dex:
    def __init__(self, name, b):
        self.name=name; self.b=b
        ss,so=u4(b,0x38),u4(b,0x3c); ts,to=u4(b,0x40),u4(b,0x44)
        fs,fo=u4(b,0x50),u4(b,0x54); ms,mo=u4(b,0x58),u4(b,0x5c)
        cs,co=u4(b,0x60),u4(b,0x64)
        def get_str(si):
            if si>=ss: return f"<s{si}>"
            off=u4(b,so+4*si); n=0;shift=0;p=off
            while True:
                x=b[p]; n|=(x&0x7f)<<shift; p+=1
                if not x&0x80: break
                shift+=7
            return b[p:p+n].decode('utf-8','replace')
        self.get_str=get_str
        self.types={i:get_str(u4(b,to+4*i)) for i in range(ts)}
        self.fields=[(self.types[u2(b,fo+8*i)],self.types[u2(b,fo+8*i+2)],get_str(u4(b,fo+8*i+4)))
                     for i in range(fs)]
        self.methods=[(self.types[u2(b,mo+8*i)],get_str(u4(b,mo+8*i+4))) for i in range(ms)]
        self.classes={self.types[u4(b,co+32*i)]:u4(b,co+32*i+24) for i in range(cs)}
    def uleb(self,p):
        n=0;shift=0
        while True:
            x=self.b[p]; n|=(x&0x7f)<<shift; p+=1
            if not x&0x80: break
            shift+=7
        return n,p
    def class_methods(self, cls):
        if cls not in self.classes: return None
        b=self.b; p=self.classes[cls]
        sf_n,p=self.uleb(p); inf_n,p=self.uleb(p)
        dm_n,p=self.uleb(p); vm_n,p=self.uleb(p)
        # walk the FIELD entries first (idx_diff, access_flags) — skipping
        # these desyncs the method walk (the CONT-47 T5 ka bug)
        for _ in range(sf_n+inf_n):
            _,p=self.uleb(p); _,p=self.uleb(p)
        def ml(n):
            out=[];midx=0
            nonlocal p
            for _ in range(n):
                d,p=self.uleb(p); midx+=d; acc,p=self.uleb(p); c,p=self.uleb(p)
                out.append((midx,acc,c))
            return out
        return ml(dm_n), ml(vm_n)
    def disasm(self, code_off):
        b=self.b
        insns_size=u4(b,code_off+12); insns_off=code_off+16
        out=[]; i=0
        def width(op,i):
            if op==0x00:
                if i+1<insns_size:
                    nxt=u2(b,insns_off+2*(i+1))
                    if nxt==0x0100: return 4+2*u2(b,insns_off+2*i+4)
                    if nxt==0x0200: return 2+4*u2(b,insns_off+2*i+2)
                    if nxt==0x0300: return 4+(u2(b,insns_off+2*i+2)*u4(b,insns_off+2*i+4)+1)//2
                return 1
            if op in W1: return 1
            if op in W2: return 2
            if op in W3: return 3
            return 2
        while i<insns_size:
            op=b[insns_off+2*i]; w=OPS.get(op)
            units=width(op,i)
            if w is None: i+=units; continue
            rb=b[insns_off+2*i+1]; a16=u2(b,insns_off+2*i+2) if units>=2 else None
            if op==0x22:
                out.append((i*2,f"new-instance {self.types.get(a16,'?')}"))
            elif op==0x20:
                out.append((i*2,f"instance-of {self.types.get(a16,'?')}"))
            elif op==0x1a:
                out.append((i*2,f"const-string \"{self.get_str(a16)[:48]}\""))
            elif op in (0x54,0x52,0x55):
                if a16<len(self.fields):
                    cd,td,fn=self.fields[a16]
                    out.append((i*2,f"iget v{rb:x}, {cd}.{fn}"))
            elif op in (0x6e,0x6f,0x70,0x71,0x72):
                cnt=(rb>>4)&0xf; fedc=u2(b,insns_off+2*i+4)
                if a16<len(self.methods):
                    cd,mn=self.methods[a16]
                    out.append((i*2,f"{w} {{{cnt}}}, {cd}.{mn}"))
            elif op in (0x74,0x75,0x76,0x77,0x78):
                a32=u4(b,insns_off+2*i+2); st=u2(b,insns_off+2*i+6)
                if a32<len(self.methods):
                    cd,mn=self.methods[a32]
                    out.append((i*2,f"{w} {{v{st}..}}, {cd}.{mn}"))
            i+=units
        return out

DEXES=[Dex(n,b) for n,b in ALL_DEXES]
print(f"loaded {len(DEXES)} dexes")

def find_class(cls):
    for d in DEXES:
        if cls in d.classes: return d
    return None

# ── pass 1: every MC method that dispatches a sendRequest* with a TL_ request
d = find_class(MC)
assert d, "MessagesController not found"
dm, vm = d.class_methods(MC)
print(f"MC methods: {len(dm)} direct + {len(vm)} virtual")
senders=[]
for midx, acc, code_off in dm+vm:
    if not code_off: continue
    cn, mn = d.methods[midx]
    if cn != MC: continue
    try:
        ins = d.disasm(code_off)
    except Exception as e:
        continue
    txt=[t for _,t in ins]
    if any('sendRequest' in t for t in txt):
        reqs=[t for t in txt if t.startswith('new-instance Lorg/telegram/tgnet/') and '$' in t]
        lams=[t for t in txt if 'new-instance' in t and ('ka;' in t or 'RequestDelegate' in t or '$External' in t or 'lambda' in t.lower())]
        if reqs:
            senders.append((mn, reqs, lams))
print(f"── MC sendRequest senders with TL_ request: {len(senders)}")
for mn, reqs, lams in senders:
    if any(k in mn for k in ('Config','config','Settings','settings')):
        print(f"  {mn}")
        for r in reqs: print(f"     REQ {r.split()[-1]}")
        for l in lams: print(f"     LAM {l.split()[-1]}")
