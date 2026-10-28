#!/usr/bin/env python3
"""CONT-47 T5 TELEGRAM: decode the MessagesController config chain.
Target: loadAppConfig / lambda$loadAppConfig$32 and loadWebBrowserConfig /
lambda$loadWebBrowserConfig$510 — the request class constructed, the
sendRequest dispatch, the lambda's instanceof check and the response fields
it reads on success. Basis: evidence/cont47/t4_tg_queue_census.json (T4).
Usage: cont47_t5_config.py"""
import sys, zipfile, struct, os

APK = os.environ.get('MA_DEX_APK', '/home/z/my-project/upload/telegram_official.apk')
MC = 'Lorg/telegram/messenger/MessagesController;'

z = zipfile.ZipFile(APK)
ALL_DEXES = [(n, z.read(n)) for n in z.namelist() if n.endswith('.dex')]
print(f"loaded {len(ALL_DEXES)} dex files")

OPS = {0x00:'nop',0x01:'move',0x02:'move/from16',0x04:'move-wide',0x07:'move-object',
       0x0a:'move-result',0x0b:'move-result-wide',0x0c:'move-result-object',
       0x0e:'return-void',0x0f:'return',0x10:'return-wide',0x11:'return-object',
       0x12:'const/4',0x13:'const/16',0x14:'const',0x15:'const/high16',
       0x16:'const-wide/16',0x17:'const-wide/32',0x18:'const-wide',
       0x1a:'const-string',0x1b:'const-string/jumbo',0x1c:'const-class',
       0x1d:'monitor-enter',0x1e:'monitor-exit',0x1f:'check-cast',0x20:'instance-of',
       0x21:'array-length',0x22:'new-instance',0x23:'new-array',0x24:'filled-new-array',
       0x26:'fill-array-data',0x27:'throw',0x28:'goto',0x29:'goto/16',0x2a:'goto/32',
       0x2b:'packed-switch',0x2c:'sparse-switch',
       0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',0x37:'if-le',
       0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez',
       0x44:'aget',0x46:'aget-object',0x4b:'aput',0x4d:'aput-object',
       0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',
       0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',0x5c:'iput-boolean',
       0x60:'sget',0x62:'sget-object',0x63:'sget-boolean',0x69:'sput-object',
       0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
       0x71:'invoke-static',0x72:'invoke-interface',
       0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',
       0x77:'invoke-static/range',0x78:'invoke-interface/range'}
W1 = {0x01,0x04,0x07} | set(range(0x0a,0x13)) | {0x1d,0x1e,0x21,0x27,0x28} | set(range(0x7b,0xb0))
W2 = {0x02,0x05,0x08,0x13,0x15,0x16,0x19,0x1a,0x1c,0x1f,0x20,0x22,0x23} | set(range(0x29,0x2d)) | set(range(0x32,0x3e)) | set(range(0x44,0x6e)) | set(range(0xd0,0xe3))
W3 = {0x03,0x06,0x09,0x14,0x17,0x1b,0x24,0x25,0x26,0x2a,0x2b,0x2c} | set(range(0x6e,0x73)) | set(range(0x74,0x79))
def u2(b,o): return struct.unpack_from('<H',b,o)[0]
def u4(b,o): return struct.unpack_from('<I',b,o)[0]

def parse_dex(b):
    ss,so = u4(b,0x38),u4(b,0x3c); ts,to = u4(b,0x40),u4(b,0x44)
    fs,fo = u4(b,0x50),u4(b,0x54); ms,mo = u4(b,0x58),u4(b,0x5c)
    cs,co = u4(b,0x60),u4(b,0x64)
    def get_str(si):
        if si>=ss: return f"<str{si}>"
        off=u4(b,so+4*si); n=0;shift=0;p=off
        while True:
            x=b[p]; n|=(x&0x7f)<<shift; p+=1
            if not x&0x80: break
            shift+=7
        return b[p:p+n].decode('utf-8','replace')
    def get_type(ti):
        if ti>=ts: return f"<type{ti}>"
        return get_str(u4(b,to+4*ti))
    fields=[(get_type(u2(b,fo+8*i)),get_type(u2(b,fo+8*i+2)),get_str(u4(b,fo+8*i+4)))
            for i in range(fs)]
    methods=[(get_type(u2(b,mo+8*i)),get_str(u4(b,mo+8*i+4))) for i in range(ms)]
    classes=[]
    for i in range(cs):
        o=co+32*i
        classes.append((get_type(u4(b,o)),u4(b,o+24)))
    return fields,methods,classes,get_str

def parse_class_data(b,cd_off):
    p=cd_off
    def uleb():
        nonlocal p
        n=0;shift=0
        while True:
            x=b[p]; n|=(x&0x7f)<<shift; p+=1
            if not x&0x80: break
            shift+=7
        return n
    uleb(); uleb()
    dm_n=uleb(); vm_n=uleb()
    def meth_list(n):
        out=[];midx=0
        for _ in range(n):
            d=uleb(); midx+=d; acc=uleb(); code_off=uleb()
            out.append((midx,acc,code_off))
        return out
    return meth_list(dm_n), meth_list(vm_n)

def disasm(b, code_off, fields, methods, get_str, interest_only=True):
    regs=u2(b,code_off); ins=u2(b,code_off+2); insns_size=u4(b,code_off+12)
    insns_off=code_off+16
    lines=[]; i=0
    def width(op,i):
        if op==0x00:
            if i+1<insns_size:
                nxt=u2(b,insns_off+2*(i+1))
                if nxt==0x0100:
                    return 4+2*u2(b,insns_off+2*i+4)
                if nxt==0x0200:
                    return 2+4*u2(b,insns_off+2*i+2)
                if nxt==0x0300:
                    return 4+(u2(b,insns_off+2*i+2)*u4(b,insns_off+2*i+4)+1)//2
            return 1
        if op in W1: return 1
        if op in W2: return 2
        if op in W3: return 3
        return 2
    while i<insns_size:
        op=b[insns_off+2*i]; w=OPS.get(op,f'op-{op:#04x}')
        units=width(op,i)
        rb=b[insns_off+2*i+1] if units>=1 else 0
        a16=u2(b,insns_off+2*i+2) if units>=2 else None
        keep=True
        if op==0x22 and a16 is not None and a16<len(fields)+10**9:  # new-instance type@
            # type idx resolves via type_ids — reuse methods list trick: we stored types only via classes
            keep=True
        if interest_only and op not in (0x22,0x1c,0x1f,0x20,0x1a,0x54,0x62,0x52,0x6e,0x6f,0x70,0x71,0x72,0x74,0x75,0x76,0x77,0x78,0x12,0x38,0x39,0x0e,0x0f,0x11,0x29):
            i+=units; continue
        desc=w
        if op in (0x1a,):
            s = get_str(a16) if a16 is not None and a16 < 10**9 else f"str@{a16}"
            # string_ids: need raw string table; get_str closure covers via parse_dex
            desc=f"const-string v{rb:#x}, \"{s[:60]}\""
        elif op in (0x1c,0x1f,0x22):
            t = TYPE_RES.get(a16, f"type@{a16:#x}")
            desc=f"{w} v{rb:#x}, {t}"
        elif op==0x20:
            t = TYPE_RES.get(a16, f"type@{a16:#x}")
            desc=f"instance-of v{(rb>>4)&0xf}, v{rb&0xf}, {t}"
        elif op in (0x52,0x53,0x54,0x55,0x59,0x5a,0x5b,0x5c,0x60,0x62,0x63,0x69):
            if a16 is not None and a16<len(fields):
                cd,td,fn=fields[a16]
                arrow='<-' if op<0x59 and op>=0x52 or op in(0x60,0x62,0x63) else '->'
                if op>=0x59 or op in (0x69,):
                    desc=f"{w} v{rb:#x} -> {cd}.{fn}:{td}"
                else:
                    desc=f"{w} v{rb:#x}, {cd}.{fn}:{td}"
        elif op in (0x6e,0x6f,0x70,0x71,0x72):
            cnt=(rb>>4)&0xf; fedc=u2(b,insns_off+2*i+4)
            rl=[fedc&0xf,(fedc>>4)&0xf,(fedc>>8)&0xf,(fedc>>12)&0xf,rb&0xf][:cnt]
            if a16 is not None and a16<len(methods):
                cd,mn=methods[a16]
                desc=f"{w} {{{','.join('v%d'%r for r in rl)}}}, {cd}.{mn}"
        elif op in (0x74,0x75,0x76,0x77,0x78):
            cnt=rb; a32=u4(b,insns_off+2*i+2) if units>=3 else None
            start=u2(b,insns_off+2*i+4)
            if a32 is not None and a32<len(methods):
                cd,mn=methods[a32]
                desc=f"{w} {{v{start}..v{start+cnt-1}}}, {cd}.{mn}"
        elif op==0x12:
            v=rb; desc=f"const/4 v{v&0xf}, #{(v>>4)&0xf if ((v>>4)&0xf)<8 else ((v>>4)&0xf)-16}"
        lines.append(f"  @{i*2:04x} {desc}")
        i+=units
    return lines, regs, ins

TYPE_RES = {}

def main():
    target_methods = sys.argv[1:] or ['loadAppConfig','lambda$loadAppConfig$32',
                                      'loadWebBrowserConfig','lambda$loadWebBrowserConfig$510']
    for name, b in ALL_DEXES:
        fields, methods, classes, get_str = parse_dex(b)
        # build type resolution from string/type tables for new-instance etc.
        ss,so=u4(b,0x38),u4(b,0x3c); ts,to=u4(b,0x40),u4(b,0x44)
        def tstr(ti):
            if ti>=ts: return f"<t{ti}>"
            si=u4(b,to+4*ti)
            if si>=ss: return f"<s{si}>"
            off=u4(b,so+4*si); n=0;shift=0;p=off
            while True:
                x=b[p]; n|=(x&0x7f)<<shift; p+=1
                if not x&0x80: break
                shift+=7
            return b[p:p+n].decode('utf-8','replace')
        TYPE_RES.clear()
        for ti in range(ts):
            TYPE_RES[ti] = tstr(ti)
        cls_map = {c:cd for c,cd in classes}
        if MC not in cls_map:
            continue
        cd_off = cls_map[MC]
        print(f"=== {MC} in {name} (class_data_off={cd_off:#x}) ===")
        dmeth, vmeth = parse_class_data(b, cd_off)
        found = {}
        for midx, acc, code_off in dmeth + vmeth:
            if midx >= len(methods): continue
            cn, mn = methods[midx]
            if cn != MC: continue
            if mn in target_methods and code_off != 0:
                found[mn] = (code_off, acc)
        for mn in target_methods:
            if mn not in found:
                print(f"--- {mn}: NOT FOUND (or abstract/native)")
                continue
            code_off, acc = found[mn]
            print(f"--- {mn} acc={acc:#x} code_off={code_off:#x}")
            # set global type resolver for disasm
            TYPE_RES.clear()
            lines, regs, ins = disasm(b, code_off, fields, methods, get_str)
            print('\n'.join(lines[:200]))
            if len(lines) > 200:
                print(f"  ... ({len(lines)} lines total, showing 200)")

if __name__ == '__main__':
    main()
