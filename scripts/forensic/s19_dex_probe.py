#!/usr/bin/env python3
"""S19 R-NEW-294 DEX ground-truth probe (binary-exact, single-DEX dooz APK).

Walks the DEX per source/dexformat.html spec, then for each target class:
  - class hierarchy (superclass + interfaces)
  - direct/virtual method inventory (name+proto)
  - optional bytecode dump with string/method/field reference resolution

Usage:
  python3 scripts/forensic/s19_dex_probe.py <apk> [--dump CLASS METHOD]...
Targets are hard-coded below (frame-clock chain, evidence for R-NEW-294).
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

# string table
strs = []
for i in range(s_sz):
    off = u4(s_off + 4 * i)
    n, p2 = uleb(off)
    strs.append(d[p2:p2 + n].decode('utf-8', 'replace'))

def type_desc(i): return strs[u4(t_off + 4 * i)]

def proto_sig(i):
    # proto_id: shorty_idx(u4)@+0, return_type_idx(u4)@+4, parameters_off(u4)@+8
    base = p_off + 12 * i
    shorty = strs[u4(base)]
    ret = type_desc(u4(base + 4))
    po = u4(base + 8)
    if po == 0:
        return shorty, [], ret
    # type_list: size(u4) followed by size × type_idx(u2)
    n = u4(po)
    params = [type_desc(u2(po + 4 + 2 * k)) for k in range(n)]
    return shorty, params, ret

def field_ref(i):
    # field_id: class_idx(u2)@0, type_idx(u2)@2, name_idx(u4)@4
    o = f_off + 8 * i
    return type_desc(u2(o)), strs[u4(o + 4)], type_desc(u2(o + 2))

def method_ref(i):
    # method_id: class_idx(u2)@0, proto_idx(u2)@2, name_idx(u4)@4
    o = m_off + 8 * i
    cls = type_desc(u2(o))
    _, params, ret = proto_sig(u2(o + 2))
    name = strs[u4(o + 4)]
    return (cls, name, params, ret)

# class defs
classes = {}
for i in range(c_sz):
    o = c_off + 32 * i
    # class_def_item (all u4): class_idx, access, super, interfaces_off,
    # source_file_idx, annotations_off, class_data_off, static_values_off
    desc = type_desc(u4(o))
    acc = u4(o + 4)
    super_idx = u4(o + 8)
    sup = type_desc(super_idx) if super_idx != 0xffffffff else '<none>'
    ifs_off = u4(o + 12)
    # interfaces are a type_list: size(u4) + entries(u2); 0 = none
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
    # NOTE: field_id_diffs are continuous across static→instance and
    # method_id_diffs across direct→virtual (dexformat.html class_data_item).
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
        prev_m = 0  # S17 VERIFIED: method idx diff RESETS per list (d8 output;
        # C++ dex_parser.cpp:791 does the same and matched every probe)
        for _ in range(n_dm if kind == 'direct' else n_vm):
            diff, p = uleb(p); af, p = uleb(p); co, p = uleb(p)
            prev_m += diff
            mr = method_ref(prev_m)
            c[kind].append((mr[0], mr[1], mr[2], mr[3], af, co))

_bad = []
for desc in list(classes):
    try:
        parse_class_data(desc)
    except Exception as ex:
        _bad.append((desc, str(ex)))
if _bad:
    print(f'[probe] {len(_bad)} classes failed to parse (skipped): {_bad[:5]}')

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

# Complete Dalvik instruction sizes (code units) by opcode — dexformat.html
SZ = {}
for o in range(0x100):
    SZ[o] = 1
# 21t (2): if-*, 22t/22b/22s/21c/21s/21h (2), 23x (2), 22c (2)
two = []
for op in list(range(0x0a, 0x0e)) + [0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x21, 0x22,
                                     0x23, 0x7b, 0x7c, 0x7d, 0x7e, 0x7f, 0x80,
                                     0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87,
                                     0x88, 0x89, 0x8a, 0x8b, 0x8c, 0x8d, 0x8e,
                                     0x8f] + list(range(0x90, 0xb0)) + \
    [0xb0, 0xb1, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6, 0xb7, 0xb8, 0xb9, 0xba,
     0xc0, 0xc1, 0xc2, 0xc3, 0xc4, 0xc5, 0xc6, 0xc7, 0xc8, 0xc9, 0xca, 0xcb,
     0xcc, 0xcd, 0xce, 0xcf, 0xd0, 0xd1, 0xd2, 0xd3, 0xd4, 0xd5, 0xd6, 0xd7,
     0xd8, 0xd9, 0xda, 0xdb, 0xdc, 0xdd, 0xde, 0xdf, 0xe0, 0xe1, 0xe2, 0xe3,
     0xe4, 0xe5, 0xe6, 0xe7, 0xe8, 0xe9, 0xea, 0xeb, 0xec, 0xed, 0xee, 0xef,
     0xf0, 0xf1, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8, 0xf9, 0xfa, 0xfb,
     0xfc, 0xfd, 0xfe, 0xff]:
    two.append(op)
two += list(range(0x01, 0x0a))      # move variants etc. (some 1-unit though)
# precise table instead:
SZ = {o: 1 for o in range(0x100)}
for o in (0x12, 0x13, 0x15, 0x16, 0x1a, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x21,
          0x22, 0x23, 0x24, 0x25, 0x26, 0x60, 0x61, 0x62, 0x63, 0x64, 0x65,
          0x66, 0x67, 0x68, 0x69, 0x6a, 0x6b, 0x6c, 0x6d, 0xd0, 0xd1, 0xd2, 0xd3,
          0xd4, 0xd5, 0xd6, 0xd7, 0xd8, 0xd9, 0xda, 0xdb, 0xdc, 0xdd, 0xde,
          0xdf, 0xe0, 0xe1, 0xe2, 0xe3, 0xe4, 0xe5, 0xe6, 0xe7, 0xe8, 0xe9,
          0xea, 0xeb, 0xec, 0xed, 0xee, 0xef, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6,
          0xf7, 0xf8, 0xf9, 0xfb, 0xfc, 0xfd, 0xfe, 0xff,
          0x02, 0x05, 0x08,  # move/from16, move-wide/from16, move-object/from16
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
    SZ[o] = 3  # invoke-* 35c/45c formats: op, method_idx, register list
for o in (0x18, 0x19, 0x1b, 0x2a, 0x2b, 0x2c):
    SZ[o] = 3
SZ[0x28] = 1  # goto 10t: offset inline in word0
for o in (0x00,):  # nop: check pseudo-insns separately
    SZ[o] = 1

def dump_code(desc, meth):
    c = classes.get(desc)
    if not c:
        print(f'== {desc}: NOT IN DEX =='); return
    for (cl, nm, params, ret, af, co) in c['direct'] + c['virtual']:
        if nm != meth or co == 0: continue
        reg_sz, ins_sz, outs_sz, tries_sz, dbg_off, insns_sz = struct.unpack_from('<HHHHII', d, co)
        print(f'--- {desc}.{meth} regs={reg_sz} ins={ins_sz} outs={outs_sz} insns_sz={insns_sz} ---')
        base = co + 16
        k = 0
        while k < insns_sz:
            cu = u2(base + 2 * k)
            op = cu & 0xff
            line = f'  {k:04x}: {cu:04x}'
            nxt = k + 1
            if op == 0x00 and (cu >> 8) >= 0x01:  # pseudo: packed/sparse/fill
                h = cu >> 8
                if h == 0x01: sz = 2 + (u2(base + 2 * (k + 1)) * 2 + 1) // 2
                elif h == 0x02: sz = 4 + u4(base + 2 * (k + 2))
                else: sz = 5 + (u4(base + 2 * (k + 2)) * 2 + 3) // 4
                line += f'  <pseudo {h:#x}>'
                nxt = k + sz
                print(line); k = nxt; continue
            if op == 0x1a and nxt < insns_sz:
                line += f'  const-string -> "{strs[u2(base + 2 * nxt)][:60]}"'
            elif op == 0x1b and nxt + 1 < insns_sz:
                idx = u2(base + 2 * nxt) | (u2(base + 2 * (nxt + 1)) << 16)
                line += f'  const-string/jumbo -> "{strs[idx][:60]}"'
            elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72) and nxt < insns_sz:
                md = method_ref(u2(base + 2 * nxt))
                kind = {0x6e: 'virtual', 0x6f: 'super', 0x70: 'direct',
                        0x71: 'static', 0x72: 'interface'}[op]
                line += f'  invoke-{kind} -> {md[0]}.{md[1]}({",".join(md[2])}){md[3]}'
            elif op in (0x74, 0x75, 0x76, 0x77, 0x78) and nxt < insns_sz:
                idx = u2(base + 2 * nxt) | (u2(base + 2 * (nxt + 1)) << 16)
                md = method_ref(idx)
                kind = {0x74: 'virtual/range', 0x75: 'super/range',
                        0x76: 'direct/range', 0x77: 'static/range',
                        0x78: 'interface/range'}[op]
                line += f'  invoke-{kind} -> {md[0]}.{md[1]}({",".join(md[2])}){md[3]}'
            elif 0x60 <= op <= 0x6d and nxt < insns_sz:
                fr = field_ref(u2(base + 2 * nxt))
                names = {0x60: 'sget', 0x61: 'sget-wide', 0x62: 'sget-object',
                         0x63: 'sget-boolean', 0x64: 'sget-byte', 0x65: 'sget-char',
                         0x66: 'sget-short', 0x67: 'sput', 0x68: 'sput-wide',
                         0x69: 'sput-object', 0x6a: 'sput-boolean', 0x6b: 'sput-byte',
                         0x6c: 'sput-char', 0x6d: 'sput-short'}
                line += f'  {names[op]} -> {fr[0]}.{fr[1]}:{fr[2]}'
            elif 0x52 <= op <= 0x5f and nxt < insns_sz:
                fr = field_ref(u2(base + 2 * nxt))
                names = {0x52: 'iget', 0x53: 'iget-wide', 0x54: 'iget-object',
                         0x55: 'iget-boolean', 0x56: 'iget-byte', 0x57: 'iget-char',
                         0x58: 'iget-short', 0x59: 'iput', 0x5a: 'iput-wide',
                         0x5b: 'iput-object', 0x5c: 'iput-boolean', 0x5d: 'iput-byte',
                         0x5e: 'iput-char', 0x5f: 'iput-short'}
                line += f'  {names[op]} -> {fr[0]}.{fr[1]}:{fr[2]}'
            elif op == 0x1f and nxt < insns_sz:
                line += f'  instance-of -> {type_desc(u2(base + 2 * nxt))}'
            elif op == 0x22 and nxt < insns_sz:
                line += f'  const-class -> {type_desc(u2(base + 2 * nxt))}'
            elif op == 0x1c and nxt < insns_sz:
                line += f'  check-cast -> {type_desc(u2(base + 2 * nxt))}'
            elif op in (0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3a, 0x3b,
                        0x3c, 0x3d) and nxt < insns_sz:
                off = u2(base + 2 * nxt)
                tgt = k + (off - 0x10000 if off >= 0x8000 else off)
                names = {0x33: 'if-eq', 0x34: 'if-ne', 0x35: 'if-lt',
                         0x36: 'if-ge', 0x37: 'if-gt', 0x38: 'if-le',
                         0x39: 'if-eqz', 0x3a: 'if-nez', 0x3b: 'if-ltz',
                         0x3c: 'if-gez', 0x3d: 'if-gtz'}
                line += f'  {names[op]} -> {tgt:04x}'
            elif op == 0x28:
                b = (cu >> 8) & 0xff
                off = b - 0x100 if b >= 0x80 else b
                line += f'  goto -> {k + off:04x}'
            elif op == 0x29 and nxt < insns_sz:
                off = u2(base + 2 * nxt)
                off = off - 0x10000 if off >= 0x8000 else off
                line += f'  goto/16 -> {k + off:04x}'
            elif op in (0x2a,) and nxt + 1 < insns_sz:
                off = u2(base + 2 * nxt) | (u2(base + 2 * (nxt + 1)) << 16)
                off = off - 0x100000000 if off >= 0x80000000 else off
                line += f'  goto/32 -> {k + off:04x}'
            elif op in (0x13, 0x16, 0x15, 0x14, 0x17):
                nm2 = {0x13: 'const/16', 0x16: 'const/4' if False else 'const/high16',
                       0x15: 'const-wide/16' if False else 'const/4' if False else 'const-wide/16',
                       0x14: 'const' if False else 'const-wide/32' if False else 'const-wide/32',
                       0x17: 'const-wide/high16'}[op]
                line += f'  {nm2}'
            print(line)
            k += SZ[op]
        return
    print(f'--- {desc}.{meth}: not found / no code ---')

targets = ['LF/d0;', 'LF/b0;', 'LF/b0$a;', 'Landroidx/compose/ui/platform/K;',
           'Landroidx/compose/ui/platform/o0;', 'LW1/j0;', 'LW1/y;', 'LR/g;',
           'LC1/a;', 'LC1/f;', 'LC1/f$a;', 'LC1/f$b;', 'LM1/i;', 'LM1/i$a;',
           'LC1/f$a$a;', 'LF/A0;', 'LF/l;', 'LF/v;', 'Lz1/g;']
for t in targets:
    show(t)

args = sys.argv[2:]
i = 0
while i < len(args):
    if args[i] == '--dump' and i + 2 < len(args):
        dump_code(args[i + 1], args[i + 2]); i += 3
    else:
        i += 1
