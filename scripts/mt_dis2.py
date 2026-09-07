#!/usr/bin/env python3
"""mt_dis2.py — correct DEX method disassembler (hand-rolled, width-exact).
Usage: python3 mt_dis2.py <apk> <class_regex> [method_regex]
"""
import struct, zipfile, sys, re

apk = sys.argv[1]
cls_pat = re.compile(sys.argv[2])
meth_pat = re.compile(sys.argv[3]) if len(sys.argv) > 3 else None

d = zipfile.ZipFile(apk).read('classes.dex')
u4 = lambda o: struct.unpack_from('<I', d, o)[0]
u2 = lambda o: struct.unpack_from('<H', d, o)[0]

str_off, str_sz = u4(0x3c), u4(0x38)
type_off, type_sz = u4(0x44), u4(0x40)
proto_off = u4(0x4c)
field_off, field_sz = u4(0x54), u4(0x50)
meth_off, meth_sz = u4(0x58), u4(0x58 - 0x58)
# fix: proper offsets
meth_sz = u4(0x58)
meth_off = u4(0x5c)
cls_off, cls_sz = u4(0x64), u4(0x60)

def uleb(p):
    r = s = 0
    while True:
        b = d[p + s]; r |= (b & 0x7f) << (7 * s); s += 1
        if not (b & 0x80): return r, p + s

def sleb(p):
    r = s = 0; cur = 0
    while True:
        b = d[p + s]; r |= (b & 0x7f) << (7 * s); s += 1; cur |= b & 0x80
        if not (b & 0x80):
            if b & 0x40: r -= (1 << (7 * s))
            return r, p + s

def S(i):
    if i >= str_sz: return '<str%d>' % i
    off = u4(str_off + 4 * i); r, p = uleb(off)
    return d[p:p + r].split(b'\x00')[0].decode('utf-8', 'replace')

def T(i): return S(u4(type_off + 4 * i)) if i < type_sz else '<t%d>' % i

def M(i):
    if i >= meth_sz: return '<m%d>' % i
    o = meth_off + 8 * i
    proto_o = proto_off + 12 * u2(o + 2)
    ret = T(u4(proto_o + 4))
    params = []
    poff = u4(proto_o + 8)
    if poff:
        n, p = uleb(poff)
        for _ in range(n):
            ti, p = uleb(p)
            params.append(T(ti))
    return '%s->%s(%s)%s' % (T(u2(o)), S(u4(o + 4)), ','.join(params), ret)

def F(i):
    if i >= field_sz: return '<f%d>' % i
    o = field_off + 8 * i
    return '%s->%s' % (T(u2(o)), S(u4(o + 4)))

# ---- instruction decoding ----
FMT = {}  # opcode -> (name, width_words, operand_fmt)
def op(code, name, w, f=None): FMT[code] = (name, w, f)

# common opcodes with exact widths
op(0x00,'nop',1); op(0x01,'move',1,'r')
for c in range(0x02,0x0a): op(c,'move/from16|wide|object%d'%c,2,'r2')
for c,n in [(0x0a,'move-result'),(0x0b,'move-result-wide'),(0x0c,'move-result-object'),(0x0d,'move-exception')]: op(c,n,1,'r')
for c in range(0x0e,0x12): op(c,'return*',1)
op(0x12,'const/4',1,'rl4'); op(0x13,'const/16',2,'rl16'); op(0x14,'const',3,'rl32')
op(0x15,'const/high16',2,'rl16'); op(0x16,'const-wide/16',2,'rl16')
op(0x17,'const-wide/32',3,'rl32'); op(0x18,'const-wide',5,'rl64'); op(0x19,'const-wide/high16',2,'rl16')
op(0x1a,'const-string',2,'rs'); op(0x1b,'const-string/jumbo',3,'rs')
op(0x1c,'const-class',2,'rt'); op(0x1d,'monitor-enter',1,'r'); op(0x1e,'monitor-exit',1,'r')
op(0x1f,'check-cast',2,'rt'); op(0x20,'instance-of',2,'r2t')
op(0x21,'array-length',1,'r2'); op(0x22,'new-instance',2,'rt'); op(0x23,'new-array',2,'r2t')
op(0x24,'filled-new-array',3,'rmeth'); op(0x25,'filled-new-array/range',3,'rrange')
op(0x26,'fill-array-data',3,'rbr')
op(0x27,'throw',1,'r'); op(0x28,'goto',1,'br8'); op(0x29,'goto/16',2,'br16'); op(0x2a,'goto/32',3,'br32')
for c,n in [(0x2b,'packed-switch'),(0x2c,'sparse-switch')]: op(c,n,3,'rbr')
for i,(c,n) in enumerate([(0x2d,'cmpl-float'),(0x2e,'cmpg-float'),(0x2f,'cmpl-double'),(0x30,'cmpg-double'),(0x31,'cmp-long')]): op(c,n,2,'r3')
for base,nm in [(0x32,'if-eq'),(0x33,'if-ne'),(0x34,'if-lt'),(0x35,'if-ge'),(0x36,'if-gt'),(0x37,'if-le')]: op(base,nm,2,'r2br')
for i,nm in enumerate(['if-eqz','if-nez','if-ltz','if-gez','if-gtz','if-lez']): op(0x38+i,nm,2,'rbr')
for c in range(0x3e,0x44): op(c,'nop%d'%c,1)
for i,nm in enumerate(['aget','aget-wide','aget-object','aget-boolean','aget-byte','aget-char','aget-short']): op(0x44+i,nm,2,'r3')
for i,nm in enumerate(['aput','aput-wide','aput-object','aput-boolean','aput-byte','aput-char','aput-short']): op(0x4b+i,nm,2,'r3')
for i,nm in enumerate(['iget','iget-wide','iget-object','iget-boolean','iget-byte','iget-char','iget-short']): op(0x52+i,nm,2,'r2f')
for i,nm in enumerate(['iput','iput-wide','iput-object','iput-boolean','iput-byte','iput-char','iput-short']): op(0x59+i,nm,2,'r2f')
for i,nm in enumerate(['sget','sget-wide','sget-object','sget-boolean','sget-byte','sget-char','sget-short']): op(0x60+i,nm,2,'rf')
for i,nm in enumerate(['sput','sput-wide','sput-object','sput-boolean','sput-byte','sput-char','sput-short']): op(0x67+i,nm,2,'rf')
for c in range(0x6e,0x72): op(c,'invoke-*%x'%c,3,'rmeth')
op(0x74,'invoke-virtual/range',3,'rrange')
for c in range(0x75,0x79): op(c,'invoke-*-range%x'%c,3,'rrange')
# binop 2addr 0xb0..0xcf width1 r2 ; binop 0xd0..0xd7 width2 ; binop/lit16 0xd8..0xe2 width2
for c in range(0x7b,0x90): op(c,'unop%x'%c,1,'r2')
for c in range(0x90,0xb0): op(c,'binop%x'%c,2,'r3')
for c in range(0xb0,0xd0): op(c,'binop2addr%x'%c,1,'r2')
for c in range(0xd0,0xd8): op(c,'binop/lit16%x'%c,2,'rrl16')
for c in range(0xd8,0xe3): op(c,'binop/lit8%x'%c,2,'rrl8')

def decode(words, code_off_abs):
    out = []
    i = 0
    n = len(words)
    while i < n:
        w = words[i]
        o = w & 0xff
        name, ww, f = FMT.get(o, ('op-%02x' % o, 1, None))
        # invoke sanity: 0x6e-0x72
        if 0x6e <= o <= 0x72:
            name = ['invoke-virtual','invoke-super','invoke-direct','invoke-static','invoke-interface'][o-0x6e]
        if i + ww > n:
            out.append('%04d: %s  <truncated>' % (i, name)); break
        txt = name
        if f == 'r':
            txt += ' v%d' % (w >> 8)
        elif f == 'r2':
            txt += ' v%d, v%d' % (w >> 8, (w >> 12) & 0xf if False else (words[i] >> 12))
        elif f == 'r3':
            txt += ' v%d, v%d, v%d' % (w >> 8, (w >> 12) & 0xf, (words[i+1] >> 12) & 0xf if False else (words[i+1] >> 12))
        elif f == 'r2t':
            txt += ' v%d, v%d, %s' % (w >> 8, (w >> 12), T(words[i+1]))
        elif f == 'rt':
            txt += ' v%d, %s' % (w >> 8, T(words[i+1]))
        elif f == 'r2f':
            txt += ' v%d, v%d, %s' % (w >> 8, (w >> 12), F(words[i+1]))
        elif f == 'rf':
            txt += ' v%d, %s' % (w >> 8, F(words[i+1]))
        elif f == 'rl4':
            txt += ' v%d, %d' % ((w >> 8) & 0xf, (w >> 12))
        elif f == 'rl16':
            txt += ' v%d, %d' % (w >> 8, struct.unpack_from('<h', struct.pack('<H', words[i+1]))[0])
        elif f == 'rl32':
            txt += ' v%d, %d' % (w >> 8, struct.unpack_from('<i', struct.pack('<I', words[i+1] | (words[i+2]<<16)))[0])
        elif f == 'rl64':
            v = struct.unpack_from('<q', struct.pack('<Q', words[i+1] | (words[i+2]<<16) | (words[i+3]<<32) | (words[i+4]<<48)))[0]
            txt += ' v%d, %d' % (w >> 8, v)
        elif f == 'rs':
            if o == 0x1a: txt += ' v%d, "%s"' % (w >> 8, S(words[i+1]))
            else: txt += ' v%d, "%s"' % (w >> 8, S(words[i+1] | (words[i+2]<<16)))
        elif f == 'rmeth':
            cnt = (w >> 12) & 0xf
            regs = []
            aw = words[i+1]
            for k in range(cnt):
                regs.append('v%d' % ((aw >> (4*k)) & 0xf))
            txt += ' {%s}, %s' % (', '.join(regs), M(words[i+2]))
        elif f == 'rrange':
            txt += ' {v%d..v%d}, %s' % (w >> 8, words[i+1], M(words[i+2]))
        elif f == 'br8':
            txt += ' %+d -> %04d' % (struct.unpack_from('<b', struct.pack('<B', w >> 8))[0], i + struct.unpack_from('<b', struct.pack('<B', w >> 8))[0])
        elif f == 'br16':
            off = struct.unpack_from('<h', struct.pack('<H', words[i+1]))[0]
            txt += ' %+d -> %04d' % (off, i + off)
        elif f == 'rbr':
            off = struct.unpack_from('<h', struct.pack('<H', words[i+1]))[0]
            txt += ' v%d, %+d -> %04d' % (w >> 8, off, i + off)
        elif f == 'r2br':
            off = struct.unpack_from('<h', struct.pack('<H', words[i+1]))[0]
            txt += ' v%d, v%d, %+d -> %04d' % (w >> 8, (w >> 12), off, i + off)
        elif f == 'rrl16':
            txt += ' v%d, v%d, %d' % (w >> 8, (w >> 12), struct.unpack_from('<h', struct.pack('<H', words[i+1]))[0])
        elif f == 'rrl8':
            txt += ' v%d, v%d, %d' % (w >> 8, (w >> 12), struct.unpack_from('<b', struct.pack('<B', words[i+1] & 0xff))[0])
        out.append('%04d: %s' % (i, txt))
        i += ww
    return out

for ci in range(cls_sz):
    off = cls_off + 32 * ci
    tn = T(u4(off))
    if not cls_pat.search(tn): continue
    cdo = u4(off + 24)
    if not cdo: continue
    p = cdo
    sf, p = uleb(p); iff, p = uleb(p); dm, p = uleb(p); vm, p = uleb(p)
    for _ in range(sf + iff):
        fi, p = uleb(p); _, p = uleb(p)
    midx = 0
    for _ in range(dm):
        d1, p = uleb(p); acc, p = uleb(p); d3, p = uleb(p); midx += d1
        if midx >= meth_sz: break
        if not d3: continue
        if meth_pat and not meth_pat.search(S(u4(meth_off + 8 * midx + 4))): continue
        o = meth_off + 8 * midx
        regs = u2(d3); ins = u2(d3 + 2); isz = u4(d3 + 12)
        insns = d[d3 + 16:d3 + 16 + isz * 2]
        words = [struct.unpack_from('<H', insns, k)[0] for k in range(0, len(insns), 2)]
        print('=' * 70)
        print('METHOD %s->%s  regs=%d ins=%d' % (tn, S(u4(o + 4)), regs, ins))
        # proto
        proto_o = proto_off + 12 * u2(o + 2)
        ret = T(u4(proto_o + 4)); params = []
        poff = u4(proto_o + 8)
        if poff:
            n2, p2 = uleb(poff)
            for _ in range(n2):
                ti, p2 = uleb(p2); params.append(T(ti))
        print('  proto: (%s) -> %s' % (','.join(params), ret))
        for line in decode(words, d3 + 16):
            print('  ' + line)
    midx = 0
    for _ in range(vm):
        d1, p = uleb(p); acc, p = uleb(p); d3, p = uleb(p); midx += d1
        if midx >= meth_sz: break
        if not d3: continue
        if meth_pat and not meth_pat.search(S(u4(meth_off + 8 * midx + 4))): continue
        o = meth_off + 8 * midx
        regs = u2(d3); ins = u2(d3 + 2); isz = u4(d3 + 12)
        insns = d[d3 + 16:d3 + 16 + isz * 2]
        words = [struct.unpack_from('<H', insns, k)[0] for k in range(0, len(insns), 2)]
        print('=' * 70)
        print('METHOD %s->%s  regs=%d ins=%d' % (tn, S(u4(o + 4)), regs, ins))
        # proto
        proto_o = proto_off + 12 * u2(o + 2)
        ret = T(u4(proto_o + 4)); params = []
        poff = u4(proto_o + 8)
        if poff:
            n2, p2 = uleb(poff)
            for _ in range(n2):
                ti, p2 = uleb(p2); params.append(T(ti))
        print('  proto: (%s) -> %s' % (','.join(params), ret))
        for line in decode(words, d3 + 16):
            print('  ' + line)
