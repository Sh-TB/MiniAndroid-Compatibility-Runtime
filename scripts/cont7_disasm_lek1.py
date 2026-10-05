#!/usr/bin/env python3
"""cont7_disasm_lek1.py — decode Lek1 (kotlinx SemaphoreImpl, R8-renamed)
from dooz classes.dex: list methods, decode target method body with
invoke/field/const-string resolution (source-first evidence for the
Semaphore ISE root, CONT-7 §13A)."""
import sys, zipfile, struct

APK = 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
z = zipfile.ZipFile(APK)
b = z.read('classes.dex')

def uleb(off):
    r = 0; s = 0
    while True:
        by = b[off]; off += 1
        r |= (by & 0x7f) << s
        if not (by & 0x80): break
        s += 7
    return r, off

string_ids_size, string_ids_off = struct.unpack_from('<II', b, 56)
type_ids_size, type_ids_off = struct.unpack_from('<II', b, 64)
proto_ids_size, proto_ids_off = struct.unpack_from('<II', b, 72)
field_ids_size, field_ids_off = struct.unpack_from('<II', b, 80)
method_ids_size, method_ids_off = struct.unpack_from('<II', b, 88)
class_defs_size, class_defs_off = struct.unpack_from('<II', b, 96)

def get_string(i):
    data_off, = struct.unpack_from('<I', b, string_ids_off + i*4)
    n, off = uleb(data_off)
    end = b.index(b'\x00', off)
    return b[off:end].decode('utf-8', 'replace')

def get_type(i):
    si, = struct.unpack_from('<I', b, type_ids_off + i*4)
    return get_string(si)

def get_field(i):
    cls, typ, name = struct.unpack_from('<HHI', b, field_ids_off + i*8)
    return get_type(cls), get_string(name)

def get_method(i):
    cls, proto, name = struct.unpack_from('<HHI', b, method_ids_off + i*8)
    return get_type(cls), get_string(name)

CLS = sys.argv[1] if len(sys.argv) > 1 else 'Lek1;'
TARGET = sys.argv[2] if len(sys.argv) > 2 else 'b'

target = None
for ci in range(class_defs_size):
    off = class_defs_off + ci*32
    cls_idx, = struct.unpack_from('<I', b, off)
    if get_type(cls_idx) == CLS:
        target = struct.unpack_from('<8I', b, off)
        break
if not target:
    print(f"class {CLS} NOT FOUND"); sys.exit(1)
(cls_idx, access, superclass, interfaces_off, source_file_idx,
 annotations_off, class_data_off, _sv) = target
print(f"class {CLS} super={get_type(superclass)}")

off = class_data_off
sf, off = uleb(off); ifs, off = uleb(off)
dm, off = uleb(off); vm, off = uleb(off)
fields = []
idx = 0
for _ in range(sf):
    d, off = uleb(off); idx += d
    fid, off = uleb(off)
    fields.append(('static',) + get_field(fid))
idx = 0
for _ in range(ifs):
    d, off = uleb(off); idx += d
    fid, off = uleb(off)
    fields.append(('inst',) + get_field(fid))
print("fields:")
for k, c, n in fields:
    print(f"  {k} {c}.{n}")

def read_methods(off, n):
    idx = 0; out = []
    for _ in range(n):
        d, off = uleb(off); idx += d
        acc, off = uleb(off)
        code_off, off = uleb(off)
        out.append((idx, acc, code_off))
    return off, out

_, direct = read_methods(*read_methods(off, 0)[::-1][::-1]) if False else (off, [])  # placeholder
off, direct = read_methods(off, dm)
off, virtual = read_methods(off, vm)

INVOKE = {0x6e: 'invoke-virtual', 0x6f: 'invoke-super', 0x70: 'invoke-direct',
          0x71: 'invoke-static', 0x72: 'invoke-interface',
          0x74: 'invoke-virtual/range', 0x76: 'invoke-direct/range',
          0x77: 'invoke-static/range', 0x78: 'invoke-interface/range'}

def decode(code_off):
    registers, ins, outs, tries, debug, insns = struct.unpack_from(
        '<HHHHII', b, code_off)
    base = code_off + 16
    print(f"  registers={registers} ins={ins} outs={outs} insns={insns}")
    i = 0
    width = {0x6e: 3, 0x6f: 3, 0x70: 3, 0x71: 3, 0x72: 3}
    while i < insns:
        unit, = struct.unpack_from('<H', b, base + i*2)
        op = unit & 0xFF
        note = ''
        size = 1
        if op in INVOKE:
            size = 3
            midx, = struct.unpack_from('<H', b, base + (i+1)*2)
            mc, mn = get_method(midx)
            note = f"{INVOKE[op]} {mc}.{mn}"
        elif op in (0x74, 0x76, 0x77, 0x78):
            size = 3
            midx, = struct.unpack_from('<H', b, base + (i+1)*2)
            mc, mn = get_method(midx)
            note = f"{INVOKE[op]} {mc}.{mn}"
        elif op in (0x1a,):  # const-string
            size = 2
            sidx, = struct.unpack_from('<H', b, base + (i+1)*2)
            note = f'const-string "{get_string(sidx)[:60]}"'
        elif op in (0x1b,):  # const-string/jumbo
            size = 3
            sidx, = struct.unpack_from('<I', b, base + (i+1)*2)
            note = f'const-string/jumbo "{get_string(sidx)[:60]}"'
        elif op in (0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5a, 0x5b, 0x5c,
                    0x5d, 0x5e, 0x5f, 0x60, 0x61, 0x62, 0x63, 0x64, 0x65):
            size = 2
            fidx, = struct.unpack_from('<H', b, base + (i+1)*2)
            fc, fn = get_field(fidx)
            names = {0x54: 'iget', 0x55: 'iget-wide', 0x56: 'iget-object',
                     0x57: 'iget-boolean', 0x5a: 'iget-char',
                     0x5b: 'iget-short', 0x59: 'iget-boolean',
                     0x5c: 'sget' if False else 'iput'}
            nm = {0x54: 'iget', 0x55: 'iget-wide', 0x56: 'iget-object',
                  0x57: 'iget-boolean', 0x58: 'iget-byte', 0x59: 'iget-char',
                  0x5a: 'iget-short', 0x5b: 'iput', 0x5c: 'iput-wide',
                  0x5d: 'iput-object', 0x5e: 'iput-boolean',
                  0x5f: 'iput-byte', 0x60: 'iput-char', 0x61: 'iput-short',
                  0x62: 'sget', 0x63: 'sget-wide', 0x64: 'sget-object',
                  0x65: 'sget-boolean'}.get(op, f'op{op:#x}')
            note = f"{nm} {fc}.{fn}"
        elif op == 0x12:
            note = 'const/4'
        elif op in (0x13, 0x16):
            size = 2
            note = 'const/16'
        elif op == 0x14:
            size = 3
            note = 'const'
        elif op == 0x15:
            size = 2
            note = 'const/high16'
        elif op in (0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, 0x11):
            names = {0x0a: 'move', 0x0b: 'move-wide', 0x0c: 'move-object',
                     0x0d: 'move-result', 0x0e: 'move-result-wide',
                     0x0f: 'move-result-object', 0x10: 'move-exception',
                     0x11: 'return-object'}
            note = names.get(op, f'op{op:#x}')
        elif op in (0x27, 0x28, 0x29, 0x2a, 0x2b, 0x2c):
            names = {0x27: 'throw', 0x28: 'goto', 0x29: 'goto/16',
                     0x2a: 'goto/32', 0x2b: 'packed-switch',
                     0x2c: 'sparse-switch'}
            note = names[op]
            if op == 0x29: size = 2
            if op in (0x2a, 0x2b, 0x2c): size = 3
        elif op in (0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
                    0x3a, 0x3b, 0x3c, 0x3d):
            size = 2
            names = {0x32: 'if-eq', 0x33: 'if-ne', 0x34: 'if-lt',
                     0x35: 'if-ge', 0x36: 'if-gt', 0x37: 'if-le',
                     0x38: 'if-eqz', 0x39: 'if-nez', 0x3a: 'if-ltz',
                     0x3b: 'if-gez', 0x3c: 'if-gtz', 0x3d: 'if-lez'}
            note = names[op]
        elif op in (0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x9b, 0x9d, 0xa0):
            size = 2
            names = {0x90: 'add-int', 0x91: 'sub-int', 0x92: 'mul-int',
                     0x93: 'div-int', 0x94: 'rem-int', 0x95: 'and-int',
                     0x9b: 'sub-long', 0x9d: 'mul-long', 0xa0: 'add-long'}
            note = names.get(op, f'arith{op:#x}')
        elif op in (0x7c, 0x7e, 0x7f, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85,
                    0x86, 0x87, 0x88, 0x89, 0x8a, 0x8b, 0x8c, 0x8d, 0x8e,
                    0x8f):
            size = 1
            note = f'unop {op:#x}'
        elif op == 0x00:
            nop, = (unit,)
            if (unit >> 8) == 0x01:
                size = 2; note = 'nop/packed-switch-payload'
            elif (unit >> 8) == 0x02:
                size = 2; note = 'nop/sparse-switch-payload'
            else:
                note = 'nop'
        if TARGET is not None and op == 0x1c:
            size = 2  # const-class
            note = 'const-class'
        print(f"  pc={i:#06x} op={op:#04x} {note}")
        i += size

print("methods:")
for midx, acc, code_off in direct + virtual:
    mc, mn = get_method(midx)
    print(f"  {mn} access=0x{acc:04x} code_off=0x{code_off:x}")
    if code_off and mn == TARGET:
        decode(code_off)
