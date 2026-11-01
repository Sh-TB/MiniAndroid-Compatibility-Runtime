#!/usr/bin/env python3
"""s141_train41_disasm.py — TRAIN-41 element-iteration law: ref-resolved disasm.

Resolves method/field/string/type ids for:
  (1) Lom;.d — the 46x materialize lambda (fast shape, ONE Lpm;.r call);
  (2) ALL callers of Lpm;.r across every class (the single-call law);
  (3) Lq;.h — the materialize folder (2 enters, factory arm never taken);
  (4) the fold law: for each resolved callee above, print the compose-runtime
      role (foldIn/foldOut/expanded/type-test) so the element-iteration hop
      that drops the keyed composed element can be pinned.
Usage: s141_train41_disasm.py <apk>
"""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location(
    'cd', '/home/z/my-project/scripts/cont9_dexdump.py')
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)

W = {}
for o in list(range(0x01, 0x0d)):
    W[o] = (1, 'x')
for o in (0x13, 0x16, 0x19):
    W[o] = (2, '21s/21h')
W[0x14] = (3, '31i'); W[0x17] = (3, '31i'); W[0x18] = (5, '51l')
for o in (0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x22, 0x23, 0x24, 0x26):
    W[o] = (2, '21c')
W[0x25] = (3, '3rc')
W[0x21] = (1, '12x')
for o in (0x2d, 0x2e, 0x2f, 0x30, 0x31):
    W[o] = (2, '23x')
for o in range(0x32, 0x38):
    W[o] = (2, '22t')
for o in range(0x38, 0x3e):
    W[o] = (2, '21t')
for o in range(0x44, 0x4f):
    W[o] = (2, '23x')
for o in range(0x4f, 0x60):
    W[o] = (2, '22c')
for o in range(0x60, 0x6d):
    W[o] = (2, '21c')
for o in range(0x6e, 0x73):
    W[o] = (3, '35c')
for o in range(0x74, 0x79):
    W[o] = (3, '3rc')
for o in range(0x7b, 0x90):
    W[o] = (1, '12x')
for o in range(0x90, 0xb0):
    W[o] = (2, '23x')
for o in range(0xb0, 0xd0):
    W[o] = (1, '12x')
for o in range(0xd0, 0xd8):
    W[o] = (2, '22s')
for o in range(0xd8, 0xe3):
    W[o] = (2, '22b')

NAMES = {
    0x00: 'nop', 0x01: 'move', 0x04: 'move-wide', 0x07: 'move-object',
    0x0a: 'move-result', 0x0b: 'move-result-wide', 0x0c: 'move-result-object',
    0x0d: 'move-exception', 0x0e: 'return-void', 0x0f: 'return',
    0x10: 'return-wide', 0x11: 'return-object', 0x12: 'const/4',
    0x13: 'const/16', 0x14: 'const', 0x16: 'const-wide/16',
    0x17: 'const-wide/32', 0x18: 'const-wide', 0x19: 'const-wide/high16',
    0x1a: 'const-string', 0x1c: 'const-class', 0x1d: 'monitor-enter',
    0x1e: 'monitor-exit', 0x1f: 'check-cast', 0x20: 'instance-of',
    0x21: 'array-length', 0x22: 'new-instance', 0x23: 'new-array',
    0x24: 'filled-new-array', 0x25: 'filled-new-array/range', 0x26: 'fill-array-data',
    0x27: 'throw', 0x28: 'goto', 0x29: 'goto/16', 0x2a: 'goto/32',
    0x2b: 'packed-switch', 0x2c: 'sparse-switch',
    0x44: 'aget', 0x45: 'aget-wide', 0x46: 'aget-object', 0x47: 'aget-boolean',
    0x48: 'aget-byte', 0x49: 'aget-char', 0x4a: 'aget-short',
    0x4b: 'aput', 0x4c: 'aput-wide', 0x4d: 'aput-object', 0x4e: 'aput-boolean',
    0x51: 'iput-wide', 0x52: 'iget', 0x53: 'iget-wide', 0x54: 'iget-object',
    0x55: 'iget-boolean', 0x56: 'iget-byte', 0x57: 'iget-char', 0x58: 'iget-short',
    0x59: 'iput-object', 0x5a: 'iput-wide', 0x5b: 'iput-boolean',
    0x5c: 'iput-byte', 0x5d: 'iput-char', 0x5e: 'iput-short',
    0x5f: 'sget', 0x60: 'sget-wide', 0x61: 'sget-object', 0x62: 'sget-boolean',
    0x63: 'sget-byte', 0x64: 'sget-char', 0x65: 'sget-short',
    0x66: 'sput', 0x67: 'sput-wide', 0x68: 'sput-object', 0x69: 'sput-boolean',
    0x6a: 'sput-byte', 0x6b: 'sput-char', 0x6c: 'sput-short',
    0x6e: 'invoke-virtual', 0x6f: 'invoke-super', 0x70: 'invoke-direct',
    0x71: 'invoke-static', 0x72: 'invoke-interface',
    0x74: 'invoke-virtual/range', 0x75: 'invoke-super/range',
    0x76: 'invoke-direct/range', 0x77: 'invoke-static/range',
    0x78: 'invoke-interface/range',
    0x7b: 'int-to-long', 0x7d: 'int-to-int', 0x81: 'int-to-char',
    0x82: 'int-to-short', 0x84: 'long-to-int', 0x85: 'long-to-float',
    0x88: 'float-to-int', 0x8b: 'double-to-int',
    0x28: 'goto',
}
K = ['int', 'long', 'float', 'double']
T = ['add', 'sub', 'mul', 'div', 'rem']
for ki, k in enumerate(K):
    for ti, t in enumerate(T):
        NAMES[0x90 + ki*5 + ti] = f'{t}-{k}'
        NAMES[0xb0 + ki*5 + ti] = f'{t}-{k}/2addr'
L = ['and', 'or', 'xor', 'shl', 'shr', 'ushr']
for i, op in enumerate(L):
    NAMES[0x95 + i] = op + '-int'; NAMES[0xa0 + i] = op + '-long'
    NAMES[0xe0 + i] = op + '-int/lit8'; NAMES[0xd6 + i] = op + '-int/lit16'
    NAMES[0xc0 + i] = op + '-int/2addr' if i < 3 else ''
NAMES[0xd0] = 'add-int/lit16'; NAMES[0xd1] = 'rsub-int'
NAMES[0xd2] = 'mul-int/lit16'; NAMES[0xd3] = 'div-int/lit16'
NAMES[0xd4] = 'rem-int/lit16'; NAMES[0xd8] = 'shl-int/lit8'
NAMES[0xd9] = 'shr-int/lit8'; NAMES[0xda] = 'ushr-int/lit8'
NAMES[0xdb] = 'add-int/lit8'; NAMES[0xdc] = 'rsub-int/lit8'
NAMES[0xdd] = 'mul-int/lit8'; NAMES[0xde] = 'div-int/lit8'
NAMES[0xdf] = 'rem-int/lit8'
for ki, k in enumerate(K):
    for i in range(6):
        pass  # 2addr long-and etc handled above


def resolve(d, op, w):
    """resolve the 16-bit ref index for 21c/22c/35c/3rc formats"""
    idx = (w >> 0) & 0xff  # placeholder; formats differ
    return None


def disasm(d, cls, meth, tag=''):
    """disassemble with ref resolution; return text lines"""
    out = []
    for i in range(d.class_defs_size):
        off = d.class_defs_off + i * 32
        if d.type_str(d.u(off, 4)) != cls:
            continue
        info = d.class_methods(off)
        for kind in ('direct', 'virtual'):
            for mname, mdesc, acc, sz, code in info[kind]:
                if mname != meth or not code:
                    continue
                insns_size = d.u(code + 12, 4)
                base = code + 16
                words = [d.u(base + 2 * w, 2) for w in range(insns_size)]
                out.append(f'{tag}{cls}.{meth}{mdesc} insns={insns_size}')
                w = 0
                while w < insns_size:
                    wd = words[w]
                    op = wd & 0xff
                    u, f = W.get(op, (1, '?'))
                    ws = ' '.join(f'{words[w+k]:04x}' for k in range(min(u, 4)))
                    nm = NAMES.get(op, f'op{op:#04x}')
                    ref = ''
                    if f in ('21c', '22c', '35c', '3rc'):
                        # ALL four formats: AA|op BBBB — index is ALWAYS the
                        # second 16-bit word (35c: A|G|op BBBB FEDC; 3rc: AA|op BBBB)
                        idx = words[w+1]
                        try:
                            mc, mn, mp = d.method_ref(idx)
                            ref = f'  -> {mc}.{mn}{mp}'
                        except Exception:
                            try:
                                fc, fn, ft = d.field_ref(idx)
                                ref = f'  -> {fc}.{fn}:{ft}'
                            except Exception:
                                ref = ''
                            if op in (0x1c, 0x1f, 0x20, 0x22, 0x23, 0x24, 0x25):
                                try:
                                    ref = f'  -> {d.type_str(idx)}'
                                except Exception:
                                    pass
                        if op in (0x1a,):
                            try:
                                ref = f'  -> "{d.string(idx)}"'
                            except Exception:
                                pass
                    out.append(f'  pc={w:3d} {nm:24s} {ws}{ref}')
                    w += u
    return out


def target_idx(d, target_cls, target_meth):
    """method_ids index for (target_cls,target_meth) — cheap single pass"""
    n = (d.string_ids_off if hasattr(d, 'string_ids_off') else 0)
    # method_ids table: we know method_ids_off; iterate it directly
    out = []
    off = d.method_ids_off
    # size: header field method_ids_size lives at header+0x58
    size = d.u(0x58, 4)
    for i in range(size):
        p = off + i * 8
        if d.type_str(d.u(p, 2)) == target_cls and d.string(d.u(p + 4, 4)) == target_meth:
            out.append(i)
    return out


def find_all(dexes, target_cls, target_meth):
    """find every (class, method, pc, op) that invokes target — index-compare"""
    callers = []
    for name, d in dexes:
        idxs = set(target_idx(d, target_cls, target_meth))
        if not idxs:
            continue
        for i in range(d.class_defs_size):
            off = d.class_defs_off + i * 32
            cdesc = d.type_str(d.u(off, 4))
            info = d.class_methods(off)
            for kind in ('direct', 'virtual'):
                for mname, mdesc, acc, sz, code in info[kind]:
                    if not code:
                        continue
                    insns_size = d.u(code + 12, 4)
                    base = code + 16
                    words = [d.u(base + 2 * w, 2) for w in range(insns_size)]
                    w = 0
                    while w < insns_size:
                        wd = words[w]
                        op = wd & 0xff
                        if op in (0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78):
                            if w + 1 < insns_size and words[w+1] in idxs:
                                callers.append((cdesc, mname, w, op))
                        u, _f = W.get(op, (1, '?'))
                        w += u
    return callers


def main():
    apk = sys.argv[1]
    z = zipfile.ZipFile(apk)
    dexes = []
    for name in z.namelist():
        if name.startswith('classes') and name.endswith('.dex'):
            dexes.append((name, cd.Dex(z.read(name))))
    print('=== (1) Lom;.d materialize lambda, ref-resolved ===')
    for ln in disasm(dexes[0][1] if dexes else None, 'Lom;', 'd', ''):
        pass
    for name, d in dexes:
        for ln in disasm(d, 'Lom;', 'd'):
            print(ln)
    print()
    print('=== (2) ALL callers of Lpm;.r ===')
    for c in find_all(dexes, 'Lpm;', 'r'):
        print(f'  caller {c[0]}.{c[1]} pc={c[2]} op={c[3]:#04x}')
    print()
    print('=== (3) ALL callers of Lpm;.c (the clickable factory body) ===')
    for c in find_all(dexes, 'Lpm;', 'c'):
        print(f'  caller {c[0]}.{c[1]} pc={c[2]} op={c[3]:#04x}')
    print()
    print('=== (4) Lq;.h materialize folder, ref-resolved ===')
    for name, d in dexes:
        for ln in disasm(d, 'Lq;', 'h'):
            print(ln)


if __name__ == '__main__':
    main()
