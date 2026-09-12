#!/usr/bin/env python3
"""S21 frame-callback gate DEX ground truth (binary-exact walker, s20 lineage).

Goals (S21 mission Phase 2):
  1. Find EVERY call site of Choreographer.postFrameCallback /
     removeFrameCallback / Handler.post* in the dooz APK, with
     class.method + pc.
  2. Dump the frame-callback class family:
     Landroidx/compose/ui/platform/J$c; (observed cb=381 runtime class),
     Landroidx/compose/ui/platform/J; (AndroidUiDispatcher),
     Landroidx/compose/ui/platform/K; (AndroidUiFrameClock).
  3. Disassemble any method on request (--dump CLASS METHOD).

Usage:
  python3 scripts/forensic/s21_frame_probe.py <apk> [--dump CLASS METHOD]... [--scan]
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
# Dalvik opcode sizes in CODE UNITS, per the official spec:
#  0x02/05/08 22x=2; 0x03/06/09 32x=3; 0x13/16/19/1a/1c/1f-23/26?; see below
#  1 unit (default): 00-01,04,07,0a-0f,11-12(const/4 11n),1d-1e(monitor 11x),
#  21(array-length 12x),27(throw 11x),28(goto 10t),7b-8f(unop 12x),b0-cf(2addr)
for o in (0x02, 0x05, 0x08,          # move/from16 family 22x
          0x13, 0x15, 0x16,          # const/16, const/high16, const-wide/16
          0x1a, 0x1c, 0x1f, 0x20, 0x22, 0x23,  # 21c/22c family
          0x29,                      # goto/16 20t
          0x2d, 0x2e, 0x2f, 0x30, 0x31,        # cmp ops 23x
          0x32, 0x33, 0x34, 0x35, 0x36, 0x37,  # if-*t 22t
          0x38, 0x39, 0x3a, 0x3b, 0x3c, 0x3d,  # if-*z 21t
          0x44, 0x45, 0x46, 0x47, 0x48, 0x49,  # aget 23x
          0x4a, 0x4b, 0x4c, 0x4d, 0x4e, 0x4f,  # aput 23x
          0x50, 0x51, 0x52, 0x53,
          0x54, 0x55, 0x56, 0x57, 0x58, 0x59,  # iget/iput 22c
          0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f,
          0x60, 0x61, 0x62, 0x63, 0x64, 0x65,  # sget/sput 21c
          0x66, 0x67, 0x68, 0x69, 0x6a, 0x6b,
          0x6c, 0x6d,
          0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9a,
          0x9b, 0x9c, 0x9d, 0x9e, 0x9f, 0xa0, 0xa1, 0xa2, 0xa3, 0xa4, 0xa5,
          0xa6, 0xa7, 0xa8, 0xa9, 0xaa, 0xab, 0xac, 0xad, 0xae, 0xaf,
          0xd0, 0xd1, 0xd2, 0xd3, 0xd4, 0xd5, 0xd6, 0xd7,      # /lit16 22s
          0xd8, 0xd9, 0xda, 0xdb, 0xdc, 0xdd, 0xde, 0xdf,      # /lit8 22b
          0xe0, 0xe1, 0xe2):
    SZ[o] = 2
for o in (0x03, 0x06, 0x09,          # move/16 family 32x
          0x14, 0x17,                # const 31i, const-wide/32 31i
          0x18,                      # const-wide 51l
          0x1b,                      # const-string/jumbo 31c
          0x24, 0x25,                # filled-new-array 35c/3rc
          0x26,                      # fill-array-data 31t
          0x2a,                      # goto/32 30t
          0x2b, 0x2c,                # packed/sparse-switch 31t
          0x6e, 0x6f, 0x70, 0x71, 0x72,        # invoke-* 35c
          0x74, 0x75, 0x76, 0x77, 0x78):       # invoke-*/range 3rc
    SZ[o] = 3
for o in (0xfa, 0xed, 0xfb, 0xfc, 0xfd, 0xfe, 0xff, 0xf2, 0xf3, 0xf4,
          0xf5, 0xf6, 0xf7, 0xf8, 0xf9):
    SZ[o] = 2   # best-effort for odex/artificial entries; not in dooz DEX

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
       0x44: 'aget', 0x45: 'aget-wide', 0x46: 'aget-object',
       0x47: 'aget-boolean', 0x48: 'aget-byte', 0x49: 'aget-char',
       0x4a: 'aget-short',
       0x4b: 'aput', 0x4c: 'aput-wide', 0x4d: 'aput-object',
       0x4e: 'aput-boolean', 0x4f: 'aput-byte', 0x50: 'aput-char',
       0x51: 'aput-short',
       0x52: 'iget', 0x53: 'iget-wide', 0x54: 'iget-object',
       0x55: 'iget-boolean', 0x56: 'iget-byte', 0x57: 'iget-char',
       0x58: 'iget-short',
       0x59: 'iput', 0x5a: 'iput-wide', 0x5b: 'iput-object',
       0x5c: 'iput-boolean', 0x5d: 'iput-byte', 0x5e: 'iput-char',
       0x5f: 'iput-short',
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
       0xfa: 'invoke-polymorphic', 0xed: 'invoke-custom'}

def dump_code(co, filter_ops=None):
    if co == 0:
        print('   (abstract/native)'); return
    # code_item header (Dalvik spec): regs u2@+0, ins u2@+2, outs u2@+4,
    # tries u2@+6, debug_info_off u4@+8, insns_size u4@+12, insns@+16.
    insns_sz = u4(co + 12)
    regs = u2(co + 0)
    ins = u2(co + 2)
    outs = u2(co + 4)
    tries = u2(co + 6)
    print(f'   registers_size={regs} ins_size={ins} outs_size={outs} tries={tries} insns_size={insns_sz}')
    base = co + 16
    pc = 0
    while pc < insns_sz:
        w = u2(base + 2 * pc)
        op = w & 0xff
        hi = w >> 8
        name = INS.get(op, f'op-{op:#04x}')
        sz = SZ.get(op, 1)
        extra = ''
        emit = True
        if op in (0x1a,):
            si = u2(base + 2 * (pc + 1))
            extra = f' "{strs[si][:60]}"'
        elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78):
            mi = u2(base + 2 * (pc + 1))
            m = method_ref(mi)
            extra = f' {m[0]}.{m[1]}({",".join(m[2])}):{m[3]}'
            if filter_ops is not None:
                emit = any(fl in m[1] for fl in filter_ops)
        elif 0x52 <= op <= 0x5f:  # iget/iput family 22c
            fi = u2(base + 2 * (pc + 1))
            f = field_ref(fi)
            extra = f' {f[0]}.{f[1]}:{f[2]}'
            if filter_ops is not None:
                emit = any(fl in f[1] for fl in filter_ops)
        elif 0x60 <= op <= 0x6d:  # sget/sput family 21c
            fi = u2(base + 2 * (pc + 1))
            f = field_ref(fi)
            extra = f' {f[0]}.{f[1]}:{f[2]}'
            if filter_ops is not None:
                emit = any(fl in f[1] for fl in filter_ops)
        elif op in (0x1c, 0x1f, 0x20, 0x22, 0x23, 0x24, 0x25):
            ti = u2(base + 2 * (pc + 1))
            extra = f' {type_desc(ti)}'
        elif op == 0x27:
            extra = f' v{hi}'
        elif op in (0x38, 0x39, 0x3a, 0x3b, 0x3c, 0x3d, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37):
            off = hi if hi < 0x8000 else hi - 0x10000
            extra = f' -> abs {pc + off}'
            if filter_ops is not None: emit = False
        elif op == 0x28:
            off = w >> 8
            if off & 0x80: off -= 0x100
            extra = f' -> {pc + off}'
            if filter_ops is not None: emit = False
        if emit:
            print(f'   {pc:#06x}: {name}{extra}')
        pc += sz

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

def scan_call_sites():
    """Every invoke-* targeting the frame-callback family + every
    iput/sget-iget touching J$c/J/K fields. Prints owner.method pc."""
    TARGETS = ('postFrameCallback', 'removeFrameCallback', 'doFrame')
    print('===== CALL-SITE SCAN (post/remove/doFrame + new-instance J$c) =====')
    for desc, c in classes.items():
        for kind in ('direct', 'virtual'):
            for (cl, nm, params, ret, af, co) in c[kind]:
                if co == 0: continue
                try:
                    insns_sz = u4(co + 12)
                    base = co + 16
                    pc = 0
                    while pc < insns_sz:
                        w = u2(base + 2 * pc)
                        op = w & 0xff
                        sz = SZ.get(op, 1)
                        if op in (0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78):
                            mi = u2(base + 2 * (pc + 1))
                            m = method_ref(mi)
                            if any(t == m[1] for t in TARGETS) or 'FrameCallback' in m[0]:
                                print(f'  {desc}.{nm} pc={pc:#06x} {op:#04x} -> {m[0]}.{m[1]}')
                        elif op == 0x22:  # new-instance
                            ti = u2(base + 2 * (pc + 1))
                            t = type_desc(ti)
                            if t in ('Landroidx/compose/ui/platform/J$c;',
                                     'Landroidx/compose/ui/platform/K$c;'):
                                print(f'  {desc}.{nm} pc={pc:#06x} new-instance {t}')
                        pc += sz
                except Exception:
                    pass

args = sys.argv[2:]
if '--scan' in args:
    scan_call_sites()
i = 0
while i < len(args):
    if args[i] == '--dump' and i + 2 < len(args):
        dump_method(args[i + 1], args[i + 2])
        i += 3
    elif args[i] == '--scan':
        i += 1
    else:
        if not args[i].startswith('--'):
            show(args[i])
        i += 1
