#!/usr/bin/env python3
"""GAME PLAYABILITY GATE — TrieNode NPE blocker DEX ground truth.

BLOCKER (A-class): with MINIANDROID_DISPATCH_ATTACH=1, dooz first composition
dies at  NPE "null cannot be cast to non-null type TrieNode" thrown in
LM1/i;.d (pc=5/17), chain K/t.s <- K/t.m <- K/f.putAll <- F/l.s0 <- F/y.b
<- androidx/compose/ui/platform/V;.a ... -> MainActivity.onCreate APP BOUNDARY.

Upstream law (compose-runtime 1.11.4, vendored kotlinx.collections.immutable):
  PersistentHashMapBuilder.putAll: node = node.mutablePutAll(map.node as TrieNode, ...)
  The Kotlin 'as TrieNode' emits Intrinsics.checkNotNull(msg="null cannot be cast...").

This probe:
  1. Dumps LM1/i;.d, LM1/i;.h, LM1/i;.c1-like cast sites — every method in
     classes LM1/i, K/f, K/t whose bytecode contains the TrieNode NPE string
     reference, with full disassembly.
  2. Dumps K/f;.putAll, K/t;.m, K/t;.s to identify their semantic identity.
  3. Lists field layout (iget/field ids) of the involved classes so the
     engine-side null-field origin can be pinned.

Usage:
  python3 scripts/forensic/gpg_trie_probe.py <apk> [class shorty ...]
  e.g.: python3 scripts/forensic/gpg_trie_probe.py dooz.apk "LM1/i;" "LK/f;" "LK/t;"
"""
import struct, sys, zipfile

apk = sys.argv[1]
wanted = [w for w in sys.argv[2:]] or ["LM1/i;", "LK/f;", "LK/t;"]
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

def field_ref(i):
    # field_id: class_idx u2, type_idx u2, name_idx u4
    cls = type_desc(u2(f_off + 8 * i))
    typ = type_desc(u2(f_off + 8 * i + 2))
    name = strs[u4(f_off + 8 * i + 4)]
    return cls, name, typ

def method_ref(i):
    # method_id: class_idx u2, proto_idx u2, name_idx u4
    cls = type_desc(u2(m_off + 8 * i))
    name = strs[u4(m_off + 8 * i + 4)]
    return cls, name

NPE_STR = "null cannot be cast to non-null type androidx.compose.runtime.external.kotlinx.collections.immutable.implementations.immutableMap.TrieNode"
npe_str_idx = set(i for i, s in enumerate(strs) if s.startswith("null cannot be cast to non-null type androidx.compose.runtime.external"))

# ---- find classes ----
class_defs = []
for i in range(c_sz):
    base = c_off + 32 * i
    class_idx = u4(base)
    access = u4(base + 4)
    superclass = u4(base + 8)
    cf_off = u4(base + 24)
    class_defs.append((type_desc(class_idx), superclass, cf_off, access))

def find_class(desc):
    for i, (cd, sup, off, acc) in enumerate(class_defs):
        if cd == desc:
            return i, sup, off, acc
    return None

# class_data parser
def parse_class_data(off):
    fields_static = []
    fields_inst = []
    methods_direct = []
    methods_virtual = []
    p = off
    sf, p = uleb(p)
    inf, p = uleb(p)
    dm, p = uleb(p)
    vm, p = uleb(p)
    idx = 0
    for _ in range(sf):
        diff, p = uleb(p); idx += diff
        acc, p = uleb(p)
        fields_static.append((idx, acc))
    idx = 0
    for _ in range(inf):
        diff, p = uleb(p); idx += diff
        acc, p = uleb(p)
        fields_inst.append((idx, acc))
    idx = 0
    for _ in range(dm):
        diff, p = uleb(p); idx += diff
        acc, p = uleb(p)
        co, p = uleb(p)
        methods_direct.append((idx, acc, co))
    idx = 0
    for _ in range(vm):
        diff, p = uleb(p); idx += diff
        acc, p = uleb(p)
        co, p = uleb(p)
        methods_virtual.append((idx, acc, co))
    return fields_static, fields_inst, methods_direct, methods_virtual

OPCODES = {
    0x00: 'nop', 0x01: 'move', 0x07: 'move-object', 0x0b: 'move-result',
    0x0c: 'move-result-object', 0x0e: 'return-void', 0x0f: 'return',
    0x10: 'return-object', 0x11: 'const/4', 0x12: 'const/16', 0x13: 'const',
    0x1a: 'const-string', 0x1c: 'const-class', 0x1f: 'check-cast',
    0x20: 'instance-of', 0x21: 'array-length', 0x22: 'new-instance',
    0x23: 'new-array', 0x24: 'filled-new-array', 0x26: 'fill-array-data',
    0x27: 'throw', 0x28: 'goto', 0x29: 'goto/16', 0x2a: 'goto/32',
    0x2b: 'packed-switch', 0x2c: 'sparse-switch', 0x2d: 'cmpl-float',
    0x31: 'cmp-long', 0x32: 'if-eq', 0x33: 'if-ne', 0x34: 'if-lt',
    0x35: 'if-ge', 0x36: 'if-gt', 0x37: 'if-le', 0x38: 'if-eqz',
    0x39: 'if-nez', 0x3a: 'if-ltz', 0x3b: 'if-gez', 0x3c: 'if-gtz',
    0x3d: 'if-lez', 0x44: 'aget', 0x46: 'aget-object', 0x4b: 'aput',
    0x4d: 'aput-object', 0x52: 'iget', 0x54: 'iget-object', 0x55: 'iget-boolean',
    0x59: 'iput', 0x5a: 'iput-object', 0x5b: 'iput-boolean',
    0x5e: 'sget', 0x60: 'sget-object', 0x62: 'sget-boolean',
    0x64: 'sput', 0x66: 'sput-object', 0x6a: 'invoke-virtual',
    0x6b: 'invoke-super', 0x6c: 'invoke-direct', 0x6d: 'invoke-static',
    0x6e: 'invoke-virtual-range', 0x6f: 'invoke-super-range',
    0x70: 'invoke-direct-range', 0x71: 'invoke-static-range',
    0x74: 'invoke-virtual', 0x75: 'invoke-super', 0x76: 'invoke-direct',
    0x77: 'invoke-static', 0x78: 'invoke-interface',
    0x79: 'invoke-interface-range', 0x0a: 'move-result-wide',
    0x08: 'move-wide', 0x16: 'const-wide/16',
}

def disasm(code_off, code_units, out):
    p = 0
    while p < code_units:
        pc = p * 2
        op = u1(code_off + p * 2)
        fmt_op = OPCODES.get(op, f'op_{op:#04x}')
        if op in (0x00,):
            # nop / payload
            if u1(code_off + p*2 + 1) == 0x03:  # packed-switch payload
                size = u2(code_off + p*2 + 2)
                p += 4 + size * 4
                continue
            if u1(code_off + p*2 + 1) == 0x02:  # sparse-switch payload
                size = u2(code_off + p*2 + 2)
                p += 2 + size * 4 + size * 2
                continue
            if u1(code_off + p*2 + 1) == 0x01:  # fill-array-data payload
                w = u2(code_off + p*2 + 4)
                sz = u4(code_off + p*2 + 8)
                p += 4 + sz * w
                continue
            out.append(f'  @{pc:04x} nop')
            p += 1
        elif op in (0x0e,):
            out.append(f'  @{pc:04x} return-void'); p += 1
        elif op in (0x0f, 0x10, 0x27, 0x21, 0x28, 0x38, 0x39, 0x3a, 0x3b, 0x3c, 0x3d,
                    0x0b, 0x0c, 0x0a, 0x1a, 0x1c, 0x1f, 0x20, 0x22, 0x23, 0x26, 0x2b, 0x2c):
            aa = u1(code_off + p*2 + 1)
            if op in (0x1a, 0x1f, 0x20, 0x22, 0x23, 0x24, 0x26, 0x2b, 0x2c, 0x1c):
                b = u2(code_off + p*2 + 2)
                if op == 0x1a:
                    out.append(f'  @{pc:04x} const-string v{aa}, "{strs[b][:60]}"')
                elif op == 0x1f:
                    out.append(f'  @{pc:04x} check-cast v{aa}, {type_desc(b)}')
                elif op == 0x20:
                    out.append(f'  @{pc:04x} instance-of v{aa}, {type_desc(b)}')
                elif op == 0x22:
                    out.append(f'  @{pc:04x} new-instance v{aa}, {type_desc(b)}')
                else:
                    out.append(f'  @{pc:04x} {fmt_op} v{aa}, @{b:#x}')
            elif op in (0x38, 0x39, 0x3a, 0x3b, 0x3c, 0x3d, 0x28):
                b = u2(code_off + p*2 + 2)
                tgt = pc + b * 2 if b < 0x8000 else pc + (b - 0x10000) * 2
                out.append(f'  @{pc:04x} {fmt_op} v{aa} -> @{tgt:04x}')
            else:
                out.append(f'  @{pc:04x} {fmt_op} v{aa}')
            p += 2
        elif op in (0x6a, 0x6b, 0x6c, 0x6d, 0x74, 0x75, 0x76, 0x77, 0x78):
            aa = u1(code_off + p*2 + 1)
            bmi = u2(code_off + p*2 + 2)
            cls, name = method_ref(bmi)
            out.append(f'  @{pc:04x} {fmt_op} {aa:04x}, {cls}.{name}')
            p += 3
        elif op in (0x6e, 0x6f, 0x70, 0x71, 0x79):
            aa = u1(code_off + p*2 + 1)
            bmi = u2(code_off + p*2 + 2)
            cls, name = method_ref(bmi)
            out.append(f'  @{pc:04x} {fmt_op} {aa:04x}, {cls}.{name}')
            p += 3
        elif op in (0x52, 0x54, 0x55, 0x59, 0x5a, 0x5b, 0x5e, 0x60, 0x62, 0x64, 0x66, 0x44, 0x46, 0x4b, 0x4d):
            aa = u1(code_off + p*2 + 1)
            bb = u1(code_off + p*2 + 2) if False else None
            fidx = u2(code_off + p*2 + 2)
            vB = u1(code_off + p*2 + 3)
            try:
                cls, name, typ = field_ref(fidx)
                out.append(f'  @{pc:04x} {fmt_op} v{aa}, v{vB}, {cls}.{name}:{typ}')
            except Exception:
                out.append(f'  @{pc:04x} {fmt_op} v{aa}, f@{fidx}')
            p += 2
        elif op in (0x11, 0x12):
            aa = u1(code_off + p*2 + 1)
            bb = u1(code_off + p*2 + 2) if op == 0x11 else u2(code_off + p*2 + 2)
            if op == 0x11:
                val = bb & 0xf if (bb >> 4) == 0 else (bb >> 4)
                out.append(f'  @{pc:04x} const/4 v{aa}, #{val}')
            else:
                out.append(f'  @{pc:04x} const/16 v{aa}, #{bb}')
            p += 2
        elif op in (0x13, 0x29):
            aa = u1(code_off + p*2 + 1)
            b = u2(code_off + p*2 + 2)
            if op == 0x13:
                out.append(f'  @{pc:04x} const v{aa}, #{b}')
            else:
                tgt = pc + b * 2 if b < 0x8000 else pc + (b - 0x10000) * 2
                out.append(f'  @{pc:04x} goto/16 -> @{tgt:04x}')
            p += 2
        elif op in (0x32, 0x33, 0x34, 0x35, 0x36, 0x37):
            aa = u1(code_off + p*2 + 1)
            bb = u1(code_off + p*2 + 2)
            b = u2(code_off + p*2 + 2) & 0  # unused
            b = u2(code_off + p*2 + 2)
            tgt = pc + b * 2 if b < 0x8000 else pc + (b - 0x10000) * 2
            out.append(f'  @{pc:04x} {fmt_op} v{aa}, v{bb} -> @{tgt:04x}')
            p += 2
        else:
            out.append(f'  @{pc:04x} {fmt_op} (raw={d[code_off+p*2:code_off+p*2+8].hex()})')
            p += 2

def dump_class_method(desc, m_idx, acc, co, npe_hits):
    # code_item: registers u2, ins u2, outs u2, tries u2, debug u4, insns u4, ...
    base = co
    regs = u2(base); ins = u2(base + 2); outs = u2(base + 4); tries = u2(base + 6)
    insns_off = base + 16
    insns_sz = u4(base + 8)
    cls, name = method_ref(m_idx)
    print(f'\n=== {desc}.{name}  regs={regs} ins={ins} outs={outs} insns={insns_sz} units ===')
    out = []
    disasm(insns_off, insns_sz, out)
    for l in out:
        mark = ' <<<NPE-STR' if any(f'@{h:04x}' in l for h in npe_hits) else ''
        print(l + mark)

for desc in wanted:
    hit = find_class(desc)
    if not hit:
        print(f'!! class {desc} NOT FOUND'); continue
    idx, sup, off, acc = hit
    print(f'\n########## CLASS {desc} super={type_desc(sup) if sup != 0xffffffff else "<none>"} ##########')
    fs, fi, md, mv = parse_class_data(off)
    print(f'  static fields: {[field_ref(i)[1]+":"+field_ref(i)[2] for i,a in fs]}')
    print(f'  instance fields: {[field_ref(i)[1]+":"+field_ref(i)[2] for i,a in fi]}')
    all_methods = [(i, a, o, 'D') for i, a, o in md] + [(i, a, o, 'V') for i, a, o in mv]
    for m_idx, macc, mco, kind in all_methods:
        cls, name = method_ref(m_idx)
        # read code to find NPE string refs
        insns_off = mco + 16
        insns_sz = u4(mco + 8)
        refs = []
        p = 0
        while p < insns_sz:
            op = u1(insns_off + p * 2)
            if op == 0x1a:  # const-string
                b = u2(insns_off + p*2 + 2)
                if b in npe_str_idx:
                    refs.append(p * 2)
            p += 1 if op == 0x00 else 2
            if op == 0x00 and u1(insns_off + p*2) in (0x01, 0x02, 0x03):
                break
        if refs or name in ('putAll', 'm', 's', 'd', 'h', 'build', 'g'):
            dump_class_method(desc, m_idx, macc, mco, refs)
