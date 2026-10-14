#!/usr/bin/env python3
"""cont18g_f268_disasm.py — CORRECT minimal DEX method disassembler (engine-pc
= 16-bit code units) for the f268 probe; resolves the throw@pc=198 mystery."""
import struct, sys, zipfile

apk_path = sys.argv[1] if len(sys.argv) > 1 else 'run/cont18g/f268.apk'
z = zipfile.ZipFile(apk_path)
dex = z.read('classes.dex')

def u4(o): return struct.unpack_from('<I', dex, o)[0]
def u2(o): return struct.unpack_from('<H', dex, o)[0]
def u1(o): return dex[o]

header = { 'string_ids': u4(0x38), 'type_ids': u4(0x40), 'proto_ids': u4(0x48),
           'field_ids': u4(0x50), 'method_ids': u4(0x58), 'class_defs': u4(0x60) }

def get_str(sid):
    off = u4(header['string_ids']*4 + 0x20 + 0)  # wrong; fix below
# proper base: data offsets are absolute in the file
def str_off(sid):
    return u4(u4(0x3C) + sid*4)
def get_str(sid):
    o = str_off(sid)
    # uleb16 size then MUTF-8
    def uleb(o):
        r=0; s=0
        while True:
            b=u1(o); o+=1
            r |= (b&0x7f)<<s; s+=7
            if not (b&0x80): return r,o
    _,o = uleb(o)
    end=dex.find(b'\x00',o)
    return dex[o:end].decode('utf-8','replace')

def type_str(tid):
    return get_str(u4(u4(0x44) + tid*4))

SIZES = {}
def setsize(rng, s):
    for o in rng: SIZES[o]=s
setsize(range(0x00,0x0c),1)
setsize(range(0x0c,0x13),1)  # move-result* , move-exception, return*
setsize(range(0x13,0x1c),2)  # const/16..const-string, check-cast etc
SIZES[0x12]=1; SIZES[0x15]=2; SIZES[0x19]=2
SIZES[0x14]=3; SIZES[0x17]=3; SIZES[0x18]=5
SIZES[0x1a]=2; SIZES[0x1b]=3; SIZES[0x1c]=2
SIZES[0x1d]=1; SIZES[0x1e]=1; SIZES[0x1f]=2; SIZES[0x20]=2
SIZES[0x21]=1; SIZES[0x22]=2; SIZES[0x23]=2
SIZES[0x24]=3; SIZES[0x25]=3; SIZES[0x26]=3; SIZES[0x27]=1
SIZES[0x28]=1; SIZES[0x29]=2; SIZES[0x2a]=3; SIZES[0x2b]=3; SIZES[0x2c]=3
setsize(range(0x2d,0x32),2)
setsize(range(0x32,0x3e),2)
setsize(range(0x3e,0x44),1)
setsize(range(0x44,0x52),2)
setsize(range(0x52,0x5e),2)
setsize(range(0x5e,0x6e),2)
setsize(range(0x6e,0x73),3)
SIZES[0x73]=1
setsize(range(0x74,0x79),3)
SIZES[0x79]=2; SIZES[0x7a]=2
setsize(range(0x7b,0x90),1)
setsize(range(0x90,0xb0),2)
setsize(range(0xb0,0xd0),1)
setsize(range(0xd0,0xe3),2)

NAMES = {0x00:'nop',0x01:'move',0x02:'move/from16',0x04:'move-wide/from16',
0x07:'move-object',0x08:'move-object/from16',0x0a:'move-result',
0x0b:'move-result-wide',0x0c:'move-result-object',0x0d:'move-exception',
0x0e:'return-void',0x0f:'return',0x11:'return-object',0x12:'const/4',
0x13:'const/16',0x14:'const',0x15:'const/high16',0x1a:'const-string',
0x1c:'const-class',0x1d:'monitor-enter',0x1e:'monitor-exit',0x1f:'check-cast',
0x20:'instance-of',0x21:'array-length',0x22:'new-instance',0x23:'new-array',
0x24:'filled-new-array',0x26:'fill-array-data',0x27:'throw',0x28:'goto',
0x29:'goto/16',0x2a:'goto/32',0x2b:'packed-switch',0x2c:'sparse-switch',
0x44:'aget',0x46:'aget-object',0x4b:'aput',0x4d:'aput-object',0x54:'iget',
0x55:'iget-wide',0x56:'iget-object',0x5a:'iput',0x5c:'sget',0x5d:'sget-wide',
0x5e:'sget-object',0x5f:'sget-boolean',0x61:'sput',0x62:'sput-wide',
0x63:'sput-object',0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
0x71:'invoke-static',0x72:'invoke-interface',0x74:'invoke-virtual/range',
0x77:'invoke-direct/range',0x78:'invoke-static/range',0x22:'new-instance'}

def method_str(mid):
    mo = u4(0x5C) + mid*4
    cls = type_str(u2(mo)); proto = u2(mo+2); name = get_str(u4(mo+4))
    return f"{cls}.{name}"

def disasm(cls_desc, meth):
    cd_off = u4(0x64)
    n = u4(0x60)
    for i in range(n):
        co = cd_off + i*32
        cdesc = type_str(u2(co))
        if cdesc != cls_desc: continue
        class_data = u4(co+24)
        # skip static/instance fields quickly: parse but ignore
        o = class_data
        def uleb(o):
            r=0;s=0
            while True:
                b=dex[o]; o+=1
                r|=(b&0x7f)<<s; s+=7
                if not (b&0x80): return r,o
        sf, o = uleb(o); ff, o = uleb(o); dm, o = uleb(o); vm, o = uleb(o)
        fid=0
        for _ in range(sf):
            d, o = uleb(o); v, o = uleb(o); fid += d
        fid=0
        for _ in range(ff):
            d, o = uleb(o); v, o = uleb(o); fid += d
        midx=0
        for _ in range(dm):
            d, o = uleb(o); midx += d
            acc, o = uleb(o); code_off, o = uleb(o)
            if method_str(midx).endswith('.'+meth+'(') or method_str(midx).split('.')[-1].split('(')[0]==meth:
                dump(code_off, meth)
        midx=0
        for _ in range(vm):
            d, o = uleb(o); midx += d
            acc, o = uleb(o); code_off, o = uleb(o)
            nm = method_str(midx).split('.')[-1].split('(')[0]
            if nm == meth:
                dump(code_off, meth)

def dump(code_off, meth):
    insns = u2(code_off+12)
    insns_off = code_off + 16
    pc = 0
    while pc < insns:
        w = u2(insns_off + pc*2)
        op = w & 0xff
        nm = NAMES.get(op, f'op0x{op:02x}')
        sz = SIZES.get(op, 1)
        extra = ''
        if op in (0x1a,):  # const-string
            idx = u2(insns_off + pc*2 + 2)
            extra = ' "%s"' % get_str(idx)[:30]
        elif op in (0x22,0x23,0x1c,0x1f,0x20):
            idx = u2(insns_off + pc*2 + 2)
            try: extra = ' %s' % type_str(idx)
            except: pass
        elif op in (0x6e,0x6f,0x70,0x71,0x72,0x74,0x77,0x78):
            idx = u2(insns_off + pc*2 + 2)
            extra = ' %s' % method_str(idx)
        elif op in (0x54,0x55,0x56,0x5a,0x5c,0x5d,0x5e,0x5f,0x61,0x62,0x63):
            idx = u2(insns_off + pc*2 + 2)
            extra = ' field@%d' % idx
        print(f'  pc={pc:4d} (0x{pc:03x}) {nm}{extra}')
        pc += sz

for m in ('rowA','rowB','rowC','rowD','rowE','onCreate'):
    print('==== METHOD', m, '====')
    disasm('Lcom/probe/f268/MainActivity;', m)
