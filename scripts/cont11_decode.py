#!/usr/bin/env python3
"""cont11_decode.py — complete correct Dalvik disassembler for one method.
Fixes cont9_dexdump's width gaps (0x2d-0x37 are cmp*, 0x38-0x3d 21t=2u,
0xa0=and-long, 0xb5=add-long/2addr, lit8 block 0xd8-0xe2, ...).
Usage: cont11_decode.py <apk> <Lcls;> <method> [width-shown-pcs]
"""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location(
    'cd', '/home/z/my-project/scripts/cont9_dexdump.py')
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)

# op -> (units, fmt)
W = {}
for o in list(range(0x01, 0x0c)):
    W[o] = (1, 'x')            # moves
W[0x0c] = (1, 'x')
for o in (0x0d, 0x0e, 0x0f, 0x10, 0x11, 0x12):
    W[o] = (1, 'x')
for o in (0x13, 0x16, 0x19):
    W[o] = (2, '21s/21h')
W[0x14] = (3, '31i')
W[0x17] = (3, '31i')
W[0x18] = (5, '51l')
for o in (0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20):
    W[o] = (2, '21c')
W[0x21] = (1, '12x')
W[0x22] = (2, '21c')
W[0x23] = (2, '22c')
W[0x24] = (3, '35c')
W[0x25] = (3, '35c')
W[0x26] = (2, '21c')
W[0x27] = (1, '11x')
W[0x28] = (1, '10t')
W[0x29] = (2, '20t')
W[0x2a] = (3, '30t')
W[0x2b] = (3, '31t')
W[0x2c] = (3, '31t')
for o in range(0x2d, 0x32):    # cmpl/cmpg/cmp-long (23x)
    W[o] = (2, '23x')
for o in range(0x32, 0x38):    # if-eq..if-le (22t)
    W[o] = (2, '22t')
for o in range(0x38, 0x3e):    # if-..z (21t)
    W[o] = (2, '21t')
for o in range(0x44, 0x4f):    # aget/aput (23x)
    W[o] = (2, '23x')
for o in range(0x4f, 0x60):    # iget/iput (22c)
    W[o] = (2, '22c')
for o in range(0x60, 0x6d):    # sget/sput (21c)
    W[o] = (2, '21c')
for o in range(0x6e, 0x73):    # invoke (35c)
    W[o] = (3, '35c')
for o in range(0x74, 0x79):    # invoke-range (3rc)
    W[o] = (3, '3rc')
for o in range(0x7b, 0x90):    # casts (12x)
    W[o] = (1, '12x')
for o in range(0x90, 0xaf):    # binop (23x)
    W[o] = (2, '23x')
for o in range(0xb0, 0xd0):    # binop/2addr (12x)
    W[o] = (1, '12x')
for o in range(0xd0, 0xd8):    # lit16 (22s)
    W[o] = (2, '22s')
for o in range(0xd8, 0xe3):    # lit8 (22b)
    W[o] = (2, '22b')

NAMES = {
    0x01: 'move', 0x04: 'move-wide', 0x07: 'move-object', 0x0a: 'move-result',
    0x0b: 'move-result-wide', 0x0c: 'move-result-object', 0x0e: 'return-void',
    0x0f: 'return', 0x10: 'return-wide', 0x11: 'return-object',
    0x12: 'const/4', 0x13: 'const/16', 0x14: 'const', 0x16: 'const-wide/16',
    0x17: 'const-wide/32', 0x18: 'const-wide', 0x19: 'const-wide/high16',
    0x1a: 'const-string', 0x1c: 'const-class', 0x1f: 'check-cast',
    0x22: 'new-instance', 0x23: 'new-array', 0x27: 'throw', 0x28: 'goto',
    0x29: 'goto/16', 0x2a: 'goto/32', 0x2b: 'packed-switch',
    0x2c: 'sparse-switch', 0x2d: 'cmpl-float', 0x2e: 'cmpg-float',
    0x2f: 'cmpl-double', 0x30: 'cmpg-double', 0x31: 'cmp-long',
    0x32: 'if-eq', 0x33: 'if-ne', 0x34: 'if-lt', 0x35: 'if-ge',
    0x36: 'if-gt', 0x37: 'if-le', 0x38: 'if-eqz', 0x39: 'if-nez',
    0x3a: 'if-ltz', 0x3b: 'if-gez', 0x3c: 'if-gtz', 0x3d: 'if-lez',
    0x44: 'aget', 0x45: 'aget-wide', 0x46: 'aget-object', 0x47: 'aget-boolean',
    0x4b: 'aput', 0x4c: 'aput-wide', 0x4d: 'aput-object',
    0x51: 'iput-wide', 0x54: 'iget-object', 0x55: 'iget-boolean',
    0x56: 'iget-byte', 0x59: 'iput-object', 0x5b: 'iput-boolean',
    0x60: 'sget', 0x62: 'sget-object', 0x69: 'sput',
    0x6e: 'invoke-virtual', 0x6f: 'invoke-super', 0x70: 'invoke-direct',
    0x71: 'invoke-static', 0x72: 'invoke-interface',
    0x74: 'invoke-virtual/range', 0x77: 'invoke-direct/range',
    0x78: 'invoke-static/range', 0x7b: 'int-to-long', 0x7d: 'int-to-int',
    0x7f: 'long-to-int', 0x81: 'int-to-char', 0x82: 'int-to-short',
    0x90: 'add-int', 0x91: 'sub-int', 0x92: 'mul-int', 0x93: 'div-int',
    0x94: 'rem-int', 0x95: 'and-int', 0x96: 'or-int', 0x97: 'xor-int',
    0x98: 'shl-int', 0x99: 'shr-int', 0x9a: 'ushr-int', 0x9b: 'add-long',
    0x9c: 'sub-long', 0x9d: 'mul-long', 0x9e: 'div-long', 0x9f: 'rem-long',
    0xa0: 'and-long', 0xa1: 'or-long', 0xa2: 'xor-long', 0xa3: 'shl-long',
    0xa4: 'shr-long', 0xa5: 'ushr-long',
    0xb0: 'add-int/2addr', 0xb1: 'sub-int/2addr', 0xb2: 'mul-int/2addr',
    0xb5: 'add-long/2addr', 0xb6: 'sub-long/2addr', 0xb7: 'mul-long/2addr',
    0xbb: 'add-float/2addr', 0xbf: 'add-double/2addr',
    0xc0: 'sub-double/2addr', 0xc1: 'mul-double/2addr',
    0xd0: 'add-int/lit16', 0xd1: 'rsub-int',
    0xd8: 'shl-int/lit8', 0xd9: 'shr-int/lit8', 0xda: 'ushr-int/lit8',
    0xdb: 'add-int/lit8', 0xdc: 'rsub-int/lit8', 0xdd: 'mul-int/lit8',
    0xde: 'div-int/lit8', 0xdf: 'rem-int/lit8', 0xe0: 'and-int/lit8',
    0xe1: 'or-int/lit8', 0xe2: 'xor-int/lit8',
}
# binop/2addr 0xb0-0xc7 family names
T = ['add', 'sub', 'mul', 'div', 'rem']
K = ['int', 'long', 'float', 'double']
for ki, k in enumerate(K):
    for ti, t in enumerate(T):
        op = 0xb0 + ki * 5 + ti
        NAMES[op] = f'{t}-{k}/2addr'
        op2 = 0x90 + ki * 5 + ti
        NAMES[op2] = f'{t}-{k}'
for op in range(0x95, 0x9b):
    NAMES[op] = ['and', 'or', 'xor', 'shl', 'shr', 'ushr'][op - 0x95] + '-int'
for op in range(0xa0, 0xa6):
    NAMES[op] = ['and', 'or', 'xor', 'shl', 'shr', 'ushr'][op - 0xa0] + '-long'


def main():
    apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
    z = zipfile.ZipFile(apk)
    for name in z.namelist():
        if not (name.startswith('classes') and name.endswith('.dex')):
            continue
        d = cd.Dex(z.read(name))
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
                    print(f'{cls}.{meth}{mdesc} insns={insns_size}')
                    w = 0
                    while w < insns_size:
                        wd = words[w]
                        op = wd & 0xff
                        u, f = W.get(op, (1, '?UNKNOWN'))
                        ws = ' '.join(f'{words[w + k]:04x}' for k in range(min(u, 4)))
                        nm = NAMES.get(op, f'op{op:#04x}')
                        print(f'  pc={w:3d} {f:8s} {nm:22s} {ws}')
                        w += u


if __name__ == '__main__':
    main()
