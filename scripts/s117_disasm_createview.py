#!/usr/bin/env python3
"""S117 — disassemble Lorg/telegram/ui/nr1;.createView around pc=120 (the
Space addView site) + list all addView call sites with their arg counts and
preceding LP construction, to pin the exact addView overload used."""
import struct, sys
sys.path.insert(0, '/home/z/my-project/scripts')
from dalvik_walker import Dex, uleb128

APK = '/home/z/my-project/upload/tg/forkgram.apk'
TARGET = 'Lorg/telegram/ui/nr1;'

import zipfile
z = zipfile.ZipFile(APK)
# find all dex parts
names = [n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]

OPCODES = {
    0x0e: ('return-void', 1), 0x0f: ('return', 1), 0x11: ('return-object', 1),
    0x12: ('const/4', 1), 0x13: ('const/16', 2), 0x14: ('const', 3),
    0x1a: ('const-string', 2), 0x1b: ('const-string/jumbo', 3),
    0x1c: ('const-class', 2), 0x22: ('new-instance', 2),
    0x23: ('new-array', 2), 0x6e: ('invoke-virtual', 3), 0x6f: ('invoke-super', 3),
    0x70: ('invoke-direct', 3), 0x71: ('invoke-static', 3),
    0x72: ('invoke-interface', 3),
    0x54: ('iget-object', 2), 0x52: ('iget', 2), 0x53: ('iget-boolean', 2),
    0x59: ('iput-object', 2), 0x57: ('iput', 2), 0x58: ('iput-boolean', 2),
    0x60: ('sget', 2), 0x61: ('sget-object', 2), 0x62: ('sget-boolean', 2),
    0x67: ('sput-wide', 2), 0x65: ('sput-object', 2), 0x63: ('sput', 2),
    0x28: ('goto', 1), 0x29: ('goto/16', 2), 0x2a: ('goto/32', 3),
    0x2b: ('packed-switch', 3), 0x2c: ('sparse-switch', 3),
    0x32: ('if-eq', 2), 0x33: ('if-ne', 2), 0x34: ('if-lt', 2),
    0x35: ('if-ge', 2), 0x36: ('if-gt', 2), 0x37: ('if-le', 2),
    0x38: ('if-eqz', 2), 0x39: ('if-nez', 2), 0x3a: ('if-ltz', 2),
    0x3b: ('if-gez', 2), 0x3c: ('if-gtz', 2), 0x3d: ('if-lez', 2),
    0xa2: ('add-long', 2), 0x90: ('add-int', 2), 0x91: ('sub-int', 2),
    0x0a: ('move-result', 1), 0x0b: ('move-result-wide', 1),
    0x0c: ('move-result-object', 1), 0x01: ('move', 1), 0x04: ('move-wide', 1),
    0x07: ('move-object', 1), 0x08: ('move-object/16', 2),
    0xb0: ('add-int/2addr', 1), 0xb1: ('sub-int/2addr', 1),
    0xd0: ('add-int/lit16', 2), 0xd7: ('add-int/lit8', 2),
    0xdd: ('sub-int/lit8', 2), 0xda: ('mul-int/lit8', 2),
    0xdb: ('mul-int/lit16', 2), 0xd8: ('mul-int/2addr', 1),
    0x8f: ('int-to-float', 1), 0x88: ('int-to-float/2addr', 1),
    0x8a: ('long-to-float', 1), 0x83: ('int-to-long', 2),
    0x84: ('int-to-long/2addr', 1), 0x85: ('long-to-int', 1),
}

def method_bytes(dex, cls, name_sub):
    off = dex.find_class(cls)
    if off is None: return []
    b = dex.b
    class_data_off, = struct.unpack_from('<I', b, off + 24)
    p = class_data_off
    sf, p = uleb128(b, p); infld, p = uleb128(b, p)
    dm, p = uleb128(b, p); vm, p = uleb128(b, p)
    for _ in range(sf): p += 2 + len(uleb128(b, p)[0:1]) and len(struct.pack('', 0)) or 0
    return (b, off, p, dm, vm)

def walk_class(dex, cls):
    off = dex.find_class(cls)
    if off is None: return None
    b = dex.b
    class_data_off, = struct.unpack_from('<I', b, off + 24)
    p = class_data_off
    def rd(p):
        v, p = uleb128(b, p); return v, p
    sf, p = rd(p); infld, p = rd(p); dmeth, p = rd(p); vmeth, p = rd(p)
    # skip fields
    for _ in range(sf):
        _, p = rd(p); _, p = rd(p)
    for _ in range(infld):
        _, p = rd(p); _, p = rd(p)
    out = []
    midx = 0
    for kind, cnt in (('direct', dmeth), ('virtual', vmeth)):
        midx = 0
        for _ in range(cnt):
            mdiff, p = rd(p)
            access, p = rd(p)
            code_off, p = rd(p)
            midx += mdiff
            mcls, mname = dex.method_at(midx)
            out.append((kind, mname, access, code_off, midx))
    return out

def disasm_method(dex, b, code_off, maxpc=400):
    if code_off == 0: return []
    regs, ins, outs, tries, dbg, insns_sz = struct.unpack_from('<HHHHII', b, code_off + 4)
    insns = code_off + 16
    pc = 0
    out = []
    while pc < min(insns_sz, maxpc):
        w0 = struct.unpack_from('<H', b, insns + pc*2)[0]
        op = w0 & 0xff
        info = OPCODES.get(op)
        if info is None:
            pc += 1
            continue
        name, words = info
        idx = 0
        if name.startswith('invoke'):
            # 35c: AGOP-BBBB
            if op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
                midx = struct.unpack_from('<H', b, insns + (pc+2)*2)[0]
                mcls, mname = dex.method_at(midx)
                # count words of args from high nibble
                nwords = (w0 >> 12) & 0xf
                out.append((pc, name, f'{mcls}->{mname}', nwords))
        elif name == 'const-string':
            si = struct.unpack_from('<H', b, insns + (pc+2)*2)[0]
            s = dex.str_at(si)
            out.append((pc, name, repr(s[:60]), 0))
        elif name in ('new-instance', 'const-class'):
            ti = struct.unpack_from('<H', b, insns + (pc+2)*2)[0]
            out.append((pc, name, dex.type_at(ti), 0))
        elif name in ('iput-object', 'iget-object', 'iput', 'iget', 'iget-boolean', 'iput-boolean', 'sget', 'sget-object', 'sget-boolean', 'sput', 'sput-object', 'sput-wide'):
            fi = struct.unpack_from('<H', b, insns + (pc+2)*2)[0]
            fcls, fname = dex.field_at(fi)
            out.append((pc, name, f'{fcls}->{fname}', 0))
        pc += words
    return out

dex = None
for n in names:
    data = z.read(n)
    d = Dex(data)
    if d.find_class(TARGET) is not None:
        dex = d
        print(f'# {TARGET} found in {n}')
        break
if dex is None:
    print('class not found'); sys.exit(1)

methods = walk_class(dex, TARGET)
for kind, mname, access, code_off, midx in methods:
    if 'createView' in mname or mname == '<init>':
        print(f'\n=== {kind} {mname} code_off=0x{code_off:x} ===')
        dis = disasm_method(dex, dex.b, code_off)
        for pc, name, detail, nw in dis:
            print(f'  pc={pc:5d} {name:22s} {detail} args_words={nw}')
