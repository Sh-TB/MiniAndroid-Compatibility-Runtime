#!/usr/bin/env python3
"""cont375_disasm_method.py — find a method's bytecode and disassemble around a pc."""
import sys, zipfile, struct

APK = sys.argv[1]
CLS = sys.argv[2]          # e.g. "Lhf1;"
METHOD = sys.argv[3]       # e.g. "<clinit>"
AROUND = int(sys.argv[4]) if len(sys.argv) > 4 else 14

z = zipfile.ZipFile(APK)
b = z.read('classes.dex')

def read_uleb(b, off):
    r = 0; s = 0
    while True:
        by = b[off]; off += 1
        r |= (by & 0x7f) << s
        if not (by & 0x80): break
        s += 7
    return r, off

# header
string_ids_size, string_ids_off = struct.unpack_from('<II', b, 56)
type_ids_size, type_ids_off = struct.unpack_from('<II', b, 64)
proto_ids_size, proto_ids_off = struct.unpack_from('<II', b, 72)
field_ids_size, field_ids_off = struct.unpack_from('<II', b, 80)
method_ids_size, method_ids_off = struct.unpack_from('<II', b, 88)
class_defs_size, class_defs_off = struct.unpack_from('<II', b, 96)

def get_string(i):
    data_off, = struct.unpack_from('<I', b, string_ids_off + i*4)
    n, off = read_uleb(b, data_off)
    end = b.index(b'\x00', off)
    return b[off:end].decode('utf-8','replace')

def get_type(i):
    si, = struct.unpack_from('<I', b, type_ids_off + i*4)
    return get_string(si)

def get_method(i):
    cls, proto, name = struct.unpack_from('<HHI', b, method_ids_off + i*8)
    return get_type(cls), get_string(name)

# find class
target = None
for ci in range(class_defs_size):
    off = class_defs_off + ci*32
    cls_idx, = struct.unpack_from('<I', b, off)
    if get_type(cls_idx) == CLS:
        target = struct.unpack_from('<IIIIIII8x', b, off) if False else struct.unpack_from('<8I', b, off)
        break
if not target:
    print(f"class {CLS} NOT FOUND in class_defs"); sys.exit(1)
(cls_idx, access, superclass, interfaces_off, source_file_idx, annotations_off, class_data_off, _static_values) = target
print(f"class {CLS} access=0x{access:04x} super={get_type(superclass) if superclass < type_ids_size or superclass==0xFFFFFFFF else '?'} class_data_off=0x{class_data_off:x}")

# parse class_data
off = class_data_off
sf, ifs = read_uleb(b, off); off2 = off
static_fields, inst_fields, direct_methods, virtual_methods = 0,0,0,0
static_fields, off = read_uleb(b, off)
inst_fields, off = read_uleb(b, off)
direct_methods, off = read_uleb(b, off)
virtual_methods, off = read_uleb(b, off)
print(f"static={static_fields} inst={inst_fields} direct={direct_methods} virtual={virtual_methods}")

def skip_fields(off, n):
    idx = 0
    for _ in range(n):
        idx, off = read_uleb(b, off)
        _, off = read_uleb(b, off)
    return off

def read_methods(off, n):
    idx = 0
    out = []
    for _ in range(n):
        diff, off = read_uleb(b, off)
        idx += diff
        access, off = read_uleb(b, off)
        code_off, off = read_uleb(b, off)
        out.append((idx, access, code_off))
    return off, out

off, direct = read_methods(off, direct_methods)
off, virtual = read_methods(off, virtual_methods)

for idx, access, code_off in direct + virtual:
    mcls, mname = get_method(idx)
    if mname != METHOD: continue
    print(f"method {mcls}.{mname} access=0x{access:04x} code_off=0x{code_off:x}")
    if code_off == 0: continue
    registers, ins, outs, tries, debug, insns = struct.unpack_from('<HHHHII', b, code_off)
    insns_size = insns
    base = code_off + 16
    print(f"registers={registers} ins={ins} insns_size={insns_size*2} bytes")
    # dump u16 units around AROUND (pc in 16-bit code units)
    start = max(0, AROUND - 12)
    end = min(insns_size, AROUND + 24)
    i = start
    while i < end:
        op = b[base + i*2]
        unit, = struct.unpack_from('<H', b, base + i*2)
        marker = ' <<<' if i == AROUND else ''
        print(f"  pc={i:#06x}: {unit:#06x} op={op:#04x}{marker}")
        i += 1
    break
