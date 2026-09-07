#!/usr/bin/env python3
"""mt_dex_disasm.py — robust DEX method disassembler for M3 forensics.
Usage: python3 mt_dex_disasm.py <apk> <class_regex> [method_regex]
Prints full bytecode words of matching methods with class context."""
import struct, zipfile, sys, re

apk, cls_pat = sys.argv[1], sys.argv[2]
meth_pat = sys.argv[3] if len(sys.argv) > 3 else ".*"
z = zipfile.ZipFile(apk)
d = z.read('classes.dex')

def u4(o): return struct.unpack_from('<I', d, o)[0]
def u2(o): return struct.unpack_from('<H', d, o)[0]
def u1(o): return d[o]

# header
str_off, str_sz = u4(0x3c), u4(0x38)
type_off, type_sz = u4(0x44), u4(0x40)
proto_off, proto_sz = u4(0x4c), u4(0x48)
field_off, field_sz = u4(0x54), u4(0x50)
meth_off, meth_sz = u4(0x5c), u4(0x58)
cls_off, cls_sz = u4(0x64), u4(0x60)

def uleb(p):
    r, s = 0, 0
    while True:
        b = u1(p + s); r |= (b & 0x7f) << (7 * s); s += 1
        if not (b & 0x80): return r, p + s

def sleb(p):
    r, s, cur = 0, 0, 0
    while True:
        b = u1(p + s); r |= (b & 0x7f) << (7 * s); s += 1; cur |= b & 0x80
        if not (b & 0x80):
            if b & 0x40: r -= (1 << (7 * s))
            return r, p + s

def get_str(idx):
    if idx >= str_sz: return '<str:%d>' % idx
    off = u4(str_off + 4 * idx)
    r, p = uleb(off)
    return d[p:p + r].split(b'\x00')[0].decode('utf-8', 'replace')

def get_type(idx):
    if idx >= type_sz: return '<type:%d>' % idx
    return get_str(u4(type_off + 4 * idx))

def get_meth(idx):
    if idx >= meth_sz: return '<meth:%d>' % idx
    o = meth_off + 8 * idx
    return "%s->%s%s" % (get_type(u2(o)), get_str(u4(o + 4)),
                         get_str(u4(proto_off + 8 * u2(o + 2) + 4)))

def get_field(idx):
    if idx >= field_sz: return '<field:%d>' % idx
    o = field_off + 8 * idx
    return "%s->%s" % (get_type(u2(o)), get_str(u4(o + 4)))  # class u16, name u32@+4

# minimal opcode table (name, fmt-width in 16-bit units)
OPS = {
 0x00:('nop',1),0x01:('move',1),0x02:('move/from16',2),0x04:('move-wide',1),
 0x07:('move-object',1),0x08:('move-object/from16',2),0x0b:('return-void',1),
 0x0c:('return',1),0x0d:('return-wide',1),0x0e:('return-object',1),
 0x0f:('const/4',1),0x10:('const/16',2),0x13:('const',3),0x14:('const-wide/16',2),
 0x16:('const-wide',3),0x18:('const-string',2),0x1a:('const-string/jumbo',3),
 0x1b:('const-class',2),0x1c:('monitor-enter',1),0x1d:('monitor-exit',1),
 0x1e:('check-cast',2),0x1f:('instance-of',2),0x20:('array-length',1),
 0x21:('new-instance',2),0x22:('new-array',2),0x23:('filled-new-array',3),
 0x26:('filled-new-array/range',3),0x27:('fill-array-data',2),
 0x28:('throw',1),0x29:('goto',1),0x2a:('goto/16',2),0x2b:('goto/32',3),
 0x2c:('packed-switch',3),0x2d:('sparse-switch',3),0x31:('cmpl-float',2),
 0x32:('if-eq',2),0x33:('if-ne',2),0x34:('if-lt',2),0x35:('if-ge',2),
 0x36:('if-gt',2),0x37:('if-le',2),0x38:('if-eqz',1),0x39:('if-nez',1),
 0x3a:('if-ltz',1),0x3b:('if-gez',1),0x3c:('if-gtz',1),0x3d:('if-lez',1),
 0x44:('aget',2),0x46:('aget-object',2),0x4b:('aput',2),0x4d:('aput-object',2),
 0x52:('iget',2),0x54:('iget-object',2),0x55:('iget-wide',2),
 0x59:('iput',2),0x5b:('iput-wide',2),0x5c:('iput-boolean',2),
 0x5f:('iput-object',2),0x60:('sget',2),0x62:('sget-object',2),
 0x63:('sget-wide',2),0x66:('sput',2),0x69:('sput-object',2),0x6a:('sput-wide',2),
 0x6e:('invoke-virtual',3),0x6f:('invoke-super',3),0x70:('invoke-direct',3),
 0x71:('invoke-static',3),0x72:('invoke-interface',3),
 0x74:('invoke-virtual/range',3),0x76:('invoke-direct/range',3),
 0x77:('invoke-static/range',3),0x78:('invoke-interface/range',3),
 0x7b:('neg-int',1),0x7d:('int-to-long',1),0x81:('long-to-int',1),
 0x82:('long-to-float',1),0x83:('long-to-double',1),0x84:('float-to-int',1),
 0x85:('float-to-long',1),0x86:('float-to-double',1),0x87:('double-to-int',1),
 0x88:('double-to-long',1),0x8a:('double-to-float',1),0x8b:('int-to-byte',1),
 0x8c:('int-to-char',1),
 0x90:('add-int',2),0x91:('sub-int',2),0x92:('mul-int',2),0x93:('div-int',2),
 0x94:('rem-int',2),0x95:('and-int',2),0x96:('or-int',2),0x97:('xor-int',2),
 0x98:('shl-int',2),0x99:('shr-int',2),0x9a:('ushr-int',2),
 0x9b:('add-long',2),0x9c:('sub-long',2),0x9d:('mul-long',2),0x9e:('div-long',2),
 0x9f:('rem-long',2),0xa0:('and-long',2),0xa1:('or-long',2),0xa2:('xor-long',2),
 0xa4:('shl-long',2),0xa5:('shr-long',2),0xa6:('ushr-long',2),
 0xa7:('add-float',2),0xa8:('sub-float',2),0xa9:('mul-float',2),
 0xaa:('div-float',2),0xab:('rem-float',2),0xac:('add-double',2),
 0xad:('sub-double',2),0xae:('mul-double',2),0xaf:('div-double',2),
 0xb0:('add-int/2addr',1),0xb1:('sub-int/2addr',1),0xb2:('mul-int/2addr',1),
 0xb3:('div-int/2addr',1),0xb4:('rem-int/2addr',1),0xb5:('and-int/2addr',1),
 0xb6:('or-int/2addr',1),0xb7:('xor-int/2addr',1),0xb8:('shl-int/2addr',1),
 0xb9:('shr-int/2addr',1),0xba:('ushr-int/2addr',1),0xbb:('add-long/2addr',1),
 0xbc:('sub-long/2addr',1),0xbd:('mul-long/2addr',1),0xbe:('div-long/2addr',1),
 0xbf:('rem-long/2addr',1),0xc0:('and-long/2addr',1),0xc1:('or-long/2addr',1),
 0xc2:('xor-long/2addr',1),0xc5:('add-float/2addr',1),0xc6:('sub-float/2addr',1),
 0xc9:('add-double/2addr',1),0xca:('sub-double/2addr',1),
 0xcd:('div-double/2addr',1),0xd0:('add-int/lit16',2),0xd1:('rsub-int',2),
 0xd2:('mul-int/lit16',2),0xd3:('div-int/lit16',2),0xd4:('rem-int/lit16',2),
 0xd5:('and-int/lit16',2),0xd6:('or-int/lit16',2),0xd7:('xor-int/lit16',2),
 0xd8:('add-int/lit8',2),0xd9:('rsub-int/lit8',2),0xda:('mul-int/lit8',2),
 0xdb:('div-int/lit8',2),0xdc:('rem-int/lit8',2),0xdd:('and-int/lit8',2),
 0xde:('or-int/lit8',2),0xdf:('xor-int/lit8',2),0xe0:('shl-int/lit8',2),
 0xe1:('shr-int/lit8',2),0xe2:('ushr-int/lit8',2),
 0xfa:('invoke-polymorphic',4),0xed:('sget-wide/jumbo',3),
}

def invoke_target(midx):
    try: return get_meth(midx)
    except Exception: return '<meth:%d>' % midx

def disasm(words):
    out = []
    i = 0
    n = len(words)
    while i < n:
        op = words[i] & 0xff
        name, w = OPS.get(op, ('op-%02x' % op, 1))
        raw = words[i:i + w]
        hexs = ' '.join('%04x' % x for x in raw)
        note = ''
        if op in (0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x76, 0x77, 0x78):
            midx = words[i + 1]
            note = '  ; ' + invoke_target(midx)
        elif op in (0x18, 0x1a):
            sidx = words[i + 1] | (words[i + 2] << 16) if op == 0x1a else words[i + 1]
            try: note = '  ; "%s"' % get_str(sidx)
            except Exception: pass
        elif op in (0x21, 0x1b, 0x1c, 0x1f):
            tidx = words[i + 1]
            try: note = '  ; ' + get_type(tidx)
            except Exception: pass
        elif op in (0x52, 0x54, 0x55, 0x59, 0x5b, 0x5c, 0x5f):
            try: note = '  ; ' + get_field(words[i + 1])
            except Exception: pass
        elif op in (0x60, 0x62, 0x63, 0x66, 0x69, 0x6a):
            try: note = '  ; ' + get_field(words[i + 1])
            except Exception: pass
        elif op in (0x2c, 0x2d, 0x27):
            if i + 1 < len(words):
                note = '  ; payload@%+d' % (words[i + 1] if words[i + 1] < 0x8000 else words[i + 1] - 0x10000)
        out.append('%04d: %-28s %s%s' % (i, name, hexs, note))
        i += w
    return '\n'.join(out)

def isz_of(d3):
    return u4(d3 + 12)

cls_re = re.compile(cls_pat)
meth_re = re.compile(meth_pat)
found = 0
for i in range(cls_sz):
    off = cls_off + 32 * i
    tn = get_type(u4(off))
    if not cls_re.search(tn): continue
    cdo = u4(off + 24)
    if not cdo: continue
    p = cdo
    sf, p = uleb(p); iff, p = uleb(p); dm, p = uleb(p); vm, p = uleb(p)
    # static fields
    fidx = 0
    for _ in range(sf):
        d1, p = uleb(p); _, p = uleb(p); fidx += d1
    # instance fields
    for _ in range(iff):
        d1, p = uleb(p); _, p = uleb(p)
        print('FIELD %s %s' % (tn, get_field(fidx)))
    midx = 0
    for _ in range(dm + vm):
        d1, p = uleb(p); d2, p = uleb(p); d3, p = uleb(p)
        midx += d1
        if midx >= meth_sz or not d3: continue
        entry = meth_off + 8 * midx
        if entry + 8 > len(d): continue
        name = get_str(u4(entry + 4))
        proto_idx = u2(entry + 2)
        access = d2
        if d3 + 16 + isz_of(d3) > len(d):
            continue
        if not meth_re.search(name): continue
        isz = u4(d3 + 12)
        insns = d[d3 + 16:d3 + 16 + isz * 2]
        words = [struct.unpack_from('<H', insns, k)[0] for k in range(0, len(insns), 2)]
        print('=' * 70)
        print('METHOD %s->%s  regs=%d ins=%d outs=%d acc=0x%x code_off=0x%x' % (
            tn, name, u2(d3), u2(d3 + 2), u2(d3 + 4), access, d3))
        print('proto: %s' % get_str(u4(proto_off + 8 * proto_idx + 4)))
        print(disasm(words))
        found += 1
print('# matched methods:', found, file=sys.stderr)
