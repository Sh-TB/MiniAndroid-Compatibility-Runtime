#!/usr/bin/env python3
"""S20 R-NEW-295 DEX ground-truth probe (binary-exact, single-DEX dooz APK).

Based on s19_dex_probe.py (S17/S19-verified DEX walker). Targets the
View-cast NPE family: LM1/i;.d (Intrinsics), Landroidx/compose/ui/platform/D;,
LF/l; (LayoutNode family), LF/v;, LF/A0;.

Usage:
  python3 s20_dex_probe.py <apk> [--dump CLASS METHOD]...
"""
import struct, sys, zipfile

apk = sys.argv[1]
z = zipfile.ZipFile(apk)
d = z.read('classes.dex')

def u4(o): return struct.unpack_from('<I', d, o)[0]
def u2(o): return struct.unpack_from('<H', d, o)[0]
def u1(o): return d[o]

s_sz, s_off = u4(0x38), u4(0x3c)
t_sz, t_off = u4(0x40), u4(0x44)
p_sz, p_off = u4(0x48), u4(0x4c)
f_sz, f_off = u4(0x50), u4(0x54)
m_sz, m_off = u4(0x58), u4(0x5c)
c_sz, c_off = u4(0x60), u4(0x64)

def uleb(p):
    r = 0; s = 0
    while True:
        b = u1(p + s); r |= (b & 0x7f) << (7 * s); s += 1
        if not (b & 0x80): return r, p + s

def sleb(p):
    r = 0; s = 0
    while True:
        b = u1(p + s); r |= (b & 0x7f) << (7 * s); s += 1
        if not (b & 0x80):
            if b & 0x40 and s < 8: r -= (1 << (7 * s))
            return r, p + s

strs = []
for i in range(s_sz):
    off = u4(s_off + 4 * i)
    n, p2 = uleb(off)
    strs.append(d[p2:p2 + n].decode('utf-8', 'replace'))

def type_desc(i): return strs[u4(t_off + 4 * i)]

def proto_sig(i):
    base = p_off + 12 * i
    shorty = strs[u4(base)]
    ret = type_desc(u4(base + 4))
    po = u4(base + 8)
    if po == 0:
        return shorty, [], ret
    n = u4(po)
    params = [type_desc(u2(po + 4 + 2 * k)) for k in range(n)]
    return shorty, params, ret

def field_ref(i):
    o = f_off + 8 * i
    return type_desc(u2(o)), strs[u4(o + 4)], type_desc(u2(o + 2))

def method_ref(i):
    o = m_off + 8 * i
    cls = type_desc(u2(o))
    _, params, ret = proto_sig(u2(o + 2))
    name = strs[u4(o + 4)]
    return (cls, name, params, ret)

classes = {}
for i in range(c_sz):
    o = c_off + 32 * i
    desc = type_desc(u4(o))
    acc = u4(o + 4)
    super_idx = u4(o + 8)
    sup = type_desc(super_idx) if super_idx != 0xffffffff else '<none>'
    ifs_off = u4(o + 12)
    interfaces = []
    if ifs_off != 0:
        n_if = u4(ifs_off)
        interfaces = [type_desc(u2(ifs_off + 4 + 2 * k)) for k in range(n_if)]
    cdo = u4(o + 24)
    classes[desc] = {'acc': acc, 'super': sup, 'if': interfaces, 'cdo': cdo,
                     'direct': [], 'virtual': [], 'sfields': [], 'ifields': []}

def parse_class_data(desc):
    c = classes[desc]
    p = c['cdo']
    if p == 0: return
    n_sf, p = uleb(p); n_if_, p = uleb(p); n_dm, p = uleb(p); n_vm, p = uleb(p)
    prev = 0
    for _ in range(n_sf):
        diff, p = uleb(p); af, p = uleb(p); prev += diff
        fr = field_ref(prev)
        c['sfields'].append((f'{fr[0]}.{fr[1]}:{fr[2]}', af))
    for _ in range(n_if_):
        diff, p = uleb(p); af, p = uleb(p); prev += diff
        fr = field_ref(prev)
        c['ifields'].append((f'{fr[0]}.{fr[1]}:{fr[2]}', af))
    for kind in ('direct', 'virtual'):
        prev_m = 0
        for _ in range(n_dm if kind == 'direct' else n_vm):
            diff, p = uleb(p); af, p = uleb(p); co, p = uleb(p)
            prev_m += diff
            mr = method_ref(prev_m)
            c[kind].append((mr[0], mr[1], mr[2], mr[3], af, co))

for desc in list(classes):
    try:
        parse_class_data(desc)
    except Exception:
        pass

def show(desc):
    c = classes.get(desc)
    if not c:
        print(f'== {desc}: NOT IN DEX ==')
        return
    print(f'== {desc} ==')
    print(f'   super={c["super"]}  interfaces={c["if"]}')
    if c['sfields']: print(f'   static fields: {c["sfields"]}')
    if c['ifields']: print(f'   instance fields: {c["ifields"]}')
    print(f'   direct methods ({len(c["direct"])}):')
    for (cl, nm, params, ret, af, co) in c['direct']:
        print(f'     - {nm}({",".join(params)}){ret} acc=0x{af:x} code_off={co}')
    print(f'   virtual methods ({len(c["virtual"])}):')
    for (cl, nm, params, ret, af, co) in c['virtual']:
        print(f'     - {nm}({",".join(params)}){ret} acc=0x{af:x} code_off={co}')

SZ = {o: 1 for o in range(0x100)}
for o in (0x12, 0x13, 0x15, 0x16, 0x1a, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x21,
          0x22, 0x23, 0x24, 0x25, 0x26, 0x60, 0x61, 0x62, 0x63, 0x64, 0x65,
          0x66, 0x67, 0x68, 0x69, 0x6a, 0x6b, 0x6c, 0x6d, 0xd0, 0xd1, 0xd2, 0xd3,
          0xd4, 0xd5, 0xd6, 0xd7, 0xd8, 0xd9, 0xda, 0xdb, 0xdc, 0xdd, 0xde,
          0xdf, 0xe0, 0xe1, 0xe2, 0xe3, 0xe4, 0xe5, 0xe6, 0xe7, 0xe8, 0xe9,
          0xea, 0xeb, 0xec, 0xed, 0xee, 0xef, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6,
          0xf7, 0xf8, 0xf9, 0xfb, 0xfc, 0xfd, 0xfe, 0xff,
          0x02, 0x05, 0x08,
          0x14, 0x17, 0x29,
          0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3a,
          0x3b, 0x3c, 0x3d, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4a, 0x4b,
          0x4c, 0x4d, 0x4e, 0x4f, 0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56,
          0x57, 0x58, 0x59, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f,
          0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9a,
          0x9b, 0x9c, 0x9d, 0x9e, 0x9f, 0xa0, 0xa1, 0xa2, 0xa3, 0xa4, 0xa5,
          0xa6, 0xa7, 0xa8, 0xa9, 0xaa, 0xab, 0xac, 0xad, 0xae, 0xaf,
          0xb0, 0xb1, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6, 0xb7, 0xb8, 0xb9, 0xba,
          0xc0, 0xc1, 0xc2, 0xc3, 0xc4, 0xc5, 0xc6, 0xc7, 0xc8, 0xc9, 0xca,
          0xcb, 0xcc, 0xcd, 0xce, 0xcf, 0x79, 0x7a,
          0x7b, 0x7c, 0x7d, 0x7e, 0x7f, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85,
          0x86, 0x87, 0x88, 0x89, 0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f):
    SZ[o] = 2
for o in (0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78):
    SZ[o] = 3
for o in (0x18, 0x19, 0x1b, 0x2a, 0x2b, 0x2c):
    SZ[o] = 3
SZ[0x28] = 1

INS = {0x00: 'nop', 0x01: 'move', 0x02: 'move/from16', 0x04: 'move-wide',
       0x07: 'move-object', 0x08: 'move-object/from16', 0x0a: 'move-result',
       0x0b: 'move-result-wide', 0x0c: 'move-result-object', 0x0d: 'move-exception',
       0x0e: 'return-void', 0x0f: 'return', 0x10: 'return-wide', 0x11: 'return-object',
       0x12: 'const/4', 0x13: 'const/16', 0x14: 'const', 0x15: 'const/high16',
       0x16: 'const-wide/16', 0x17: 'const-wide/32', 0x18: 'const-wide',
       0x19: 'const-wide/high16', 0x1a: 'const-string', 0x1b: 'const-string/jumbo',
       0x1c: 'const-class', 0x1d: 'monitor-enter', 0x1e: 'monitor-exit',
       0x1f: 'check-cast', 0x20: 'instance-of', 0x21: 'array-length',
       0x22: 'new-instance', 0x23: 'new-array', 0x24: 'filled-new-array',
       0x25: 'filled-new-array/range', 0x26: 'fill-packed-array',
       0x27: 'throw', 0x28: 'goto', 0x29: 'goto/16', 0x2a: 'goto/32',
       0x2b: 'packed-switch', 0x2c: 'sparse-switch',
       0x2d: 'cmpl-float', 0x2e: 'cmpg-float', 0x2f: 'cmpl-double',
       0x30: 'cmpg-double', 0x31: 'cmp-long',
       0x32: 'if-eq', 0x33: 'if-ne', 0x34: 'if-lt', 0x35: 'if-ge',
       0x36: 'if-gt', 0x37: 'if-le', 0x38: 'if-eqz', 0x39: 'if-nez',
       0x3a: 'if-ltz', 0x3b: 'if-gez', 0x3c: 'if-gtz', 0x3d: 'if-lez',
       0x44: 'aget', 0x4a: 'aget-object', 0x4b: 'aget-boolean', 0x4e: 'aget-int',
       0x4f: 'aget-wide', 0x54: 'iget', 0x55: 'iget-wide', 0x56: 'iget-object',
       0x57: 'iget-boolean', 0x59: 'iget-int', 0x5b: 'iput', 0x5c: 'iput-wide',
       0x5d: 'iput-object', 0x5e: 'iput-boolean', 0x5f: 'iput-byte',
       0x60: 'sget', 0x61: 'sget-wide', 0x62: 'sget-object', 0x63: 'sget-boolean',
       0x64: 'sget-byte', 0x65: 'sget-char', 0x66: 'sget-short',
       0x67: 'sput', 0x68: 'sput-wide', 0x69: 'sput-object', 0x6a: 'sput-boolean',
       0x6b: 'sput-byte', 0x6c: 'sput-char', 0x6d: 'sput-short',
       0x6e: 'invoke-virtual', 0x6f: 'invoke-super', 0x70: 'invoke-direct',
       0x71: 'invoke-static', 0x72: 'invoke-interface',
       0x74: 'invoke-virtual/range', 0x75: 'invoke-super/range',
       0x76: 'invoke-direct/range', 0x77: 'invoke-static/range',
       0x78: 'invoke-interface/range',
       0x7b: 'int-to-long', 0x7c: 'int-to-float', 0x7d: 'int-to-double',
       0x81: 'long-to-int', 0x83: 'long-to-double', 0x85: 'float-to-int',
       0x88: 'double-to-int', 0x8f: 'int-to-byte',
       0x90: 'add-int', 0x91: 'sub-int', 0x92: 'mul-int', 0x93: 'div-int',
       0x94: 'rem-int', 0x95: 'and-int', 0x96: 'or-int', 0x97: 'xor-int',
       0x98: 'shl-int', 0x99: 'shr-int', 0x9a: 'ushr-int',
       0x9b: 'add-long', 0x9c: 'sub-long', 0x9d: 'mul-long', 0x9e: 'div-long',
       0x9f: 'rem-long', 0xa0: 'and-long', 0xa1: 'or-long', 0xa2: 'xor-long',
       0xa3: 'shl-long', 0xa4: 'shr-long', 0xa5: 'ushr-long',
       0xa6: 'add-float', 0xa7: 'sub-float', 0xa8: 'mul-float', 0xa9: 'div-float',
       0xaa: 'add-double', 0xab: 'sub-double', 0xac: 'mul-double', 0xad: 'div-double',
       0xb0: 'add-int/2addr', 0xb1: 'sub-int/2addr', 0xb2: 'mul-int/2addr',
       0xb3: 'div-int/2addr', 0xb4: 'rem-int/2addr', 0xb5: 'and-int/2addr',
       0xb6: 'or-int/2addr', 0xb7: 'xor-int/2addr', 0xb8: 'shl-int/2addr',
       0xb9: 'shr-int/2addr', 0xba: 'ushr-int/2addr',
       0xbb: 'add-long/2addr', 0xbc: 'sub-long/2addr', 0xbd: 'mul-long/2addr',
       0xbe: 'div-long/2addr', 0xbf: 'rem-long/2addr',
       0xc0: 'add-float/2addr', 0xc1: 'sub-float/2addr', 0xc2: 'mul-float/2addr',
       0xc3: 'div-float/2addr',
       0xc4: 'add-double/2addr', 0xc5: 'sub-double/2addr', 0xc6: 'mul-double/2addr',
       0xc7: 'div-double/2addr',
       0xd0: 'add-int/lit16', 0xd1: 'rsub-int', 0xd2: 'mul-int/lit16',
       0xd3: 'div-int/lit16', 0xd4: 'rem-int/lit16', 0xd5: 'and-int/lit16',
       0xd6: 'or-int/lit16', 0xd7: 'xor-int/lit16',
       0xd8: 'add-int/lit8', 0xd9: 'rsub-int/lit8', 0xda: 'mul-int/lit8',
       0xdb: 'div-int/lit8', 0xdc: 'rem-int/lit8', 0xdd: 'and-int/lit8',
       0xde: 'or-int/lit8', 0xdf: 'xor-int/lit8', 0xe0: 'shl-int/lit8',
       0xe1: 'shr-int/lit8', 0xe2: 'ushr-int/lit8',
       0xfa: 'invoke-polymorphic', 0xed: 'invoke-custom',
       0xf2: 'iget-quick', 0xf3: 'iget-wide-quick', 0xf4: 'iget-object-quick',
       0xf5: 'iget-boolean-quick', 0xf6: 'iget-char-quick',
       0xf7: 'iget-byte-quick', 0xf8: 'iget-short-quick',
       0xf9: 'iput-quick', 0xfa2: 'iput-wide-quick'}

def dump_method(cls, meth):
    c = classes.get(cls)
    if not c:
        print(f'== {cls}: NOT IN DEX =='); return
    found = False
    for kind in ('direct', 'virtual'):
        for (cl, nm, params, ret, af, co) in c[kind]:
            if nm == meth:
                found = True
                print(f'== {cls}.{meth}({",".join(params)}){ret} [{kind}] code_off={co} ==')
                dump_code(co)
                break
        if found: break
    if not found:
        print(f'== {cls}.{meth}: METHOD NOT FOUND ==')

def dump_code(co):
    if co == 0:
        print('   (abstract/native)'); return
    insns_sz = u4(co + 12)
    regs = u2(co + 8)
    ins = u2(co + 10)
    print(f'   registers_size={regs} ins_size={ins} insns_size={insns_sz}')
    base = co + 16
    pc = 0
    while pc < insns_sz:
        w = u2(base + 2 * pc)
        op = w & 0xff
        hi = w >> 8
        name = INS.get(op, f'op-{op:#04x}')
        sz = SZ.get(op, 1)
        extra = ''
        if op in (0x1a,):  # const-string
            si = u2(base + 2 * (pc + 1))
            extra = f' "{strs[si][:60]}"'
        elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
            mi = u2(base + 2 * (pc + 1))
            m = method_ref(mi)
            extra = f' {m[0]}.{m[1]}({",".join(m[2])}):{m[3]}'
        elif op in (0x74, 0x75, 0x76, 0x77, 0x78):
            mi = u2(base + 2 * (pc + 1))
            m = method_ref(mi)
            extra = f' {m[0]}.{m[1]}({",".join(m[2])}):{m[3]}'
        elif op in (0x54, 0x56, 0x57, 0x59, 0x5b, 0x5d, 0x5e):
            fi = u2(base + 2 * (pc + 1))
            f = field_ref(fi)
            extra = f' {f[0]}.{f[1]}:{f[2]}'
        elif op in (0x60, 0x62, 0x63, 0x67, 0x69, 0x6a):
            fi = u2(base + 2 * (pc + 1))
            f = field_ref(fi)
            extra = f' {f[0]}.{f[1]}:{f[2]}'
        elif op in (0x1c, 0x1f, 0x20, 0x22, 0x23, 0x24, 0x25):
            ti = u2(base + 2 * (pc + 1))
            extra = f' {type_desc(ti)}'
        elif op in (0x27,):
            extra = f' v{hi}'
        elif op in (0x38, 0x39, 0x3a, 0x3b, 0x3c, 0x3d):
            off = hi if hi < 0x8000 else hi - 0x10000
            extra = f' -> +{off} (abs {pc + off})'
        elif op in (0x32, 0x33, 0x34, 0x35, 0x36, 0x37):
            off = hi if hi < 0x8000 else hi - 0x10000
            extra = f' -> +{off} (abs {pc + off})'
        elif op == 0x28:
            off = w >> 8
            if off & 0x80: off -= 0x100
            extra = f' -> {pc + off}'
        elif op == 0x0f or op == 0x11 or op == 0x0e:
            pass
        print(f'   {pc:#06x}: {name}{extra}')
        pc += sz

args = sys.argv[2:]
if not args:
    for cls in ('LM1/i;', 'Landroidx/compose/ui/platform/D;', 'LF/l;', 'LF/v;', 'LF/A0;'):
        show(cls)
else:
    i = 0
    while i < len(args):
        if args[i] == '--dump' and i + 2 < len(args):
            dump_method(args[i + 1], args[i + 2])
            i += 3
        else:
            show(args[i]) if not args[i].startswith('--') else None
            i += 1
