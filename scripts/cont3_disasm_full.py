#!/usr/bin/env python3
"""cont3_disasm_full.py — full-fidelity method disassembler for CONT-3.

Fixes the cont375_disasm_method.py class_data header double-read bug and
decodes operands for the opcodes relevant to the Lo;.b pc=52 investigation.

Usage: cont3_disasm_full.py <apk> <Lcls;> <method> [pc_lo] [pc_hi]
"""
import sys, zipfile, struct

APK = sys.argv[1]
CLS = sys.argv[2]
METHOD = sys.argv[3]
PC_LO = int(sys.argv[4], 0) if len(sys.argv) > 4 else None
PC_HI = int(sys.argv[5], 0) if len(sys.argv) > 5 else None

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
    return get_type(cls), get_type(typ), get_string(name)

def get_method(i):
    cls, proto, name = struct.unpack_from('<HHI', b, method_ids_off + i*8)
    # proto_id: shorty_idx(u32), return_type_idx(u32), parameters_off(u32)
    ps, rt, params = struct.unpack_from('<III', b, proto_ids_off + proto*12)
    if params == 0:
        plist = []
    else:
        size, = struct.unpack_from('<I', b, params)
        plist = [get_type(struct.unpack_from('<H', b, params + 4 + k*2)[0]) for k in range(size)]
    return get_type(cls), get_string(name), get_type(rt), plist

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
print(f"class {CLS} access=0x{access:04x} super={get_type(superclass)} class_data_off=0x{class_data_off:x}")

off = class_data_off
static_fields, off = uleb(off)
inst_fields, off = uleb(off)
direct_methods, off = uleb(off)
virtual_methods, off = uleb(off)
print(f"static={static_fields} inst={inst_fields} direct={direct_methods} virtual={virtual_methods}")

def skip_fields(off, n):
    for _ in range(n):
        _, off = uleb(off)
        _, off = uleb(off)
    return off

off = skip_fields(off, static_fields + inst_fields)

def read_methods(off, n):
    idx = 0; out = []
    for _ in range(n):
        diff, off = uleb(off)
        idx += diff
        access, off = uleb(off)
        code_off, off = uleb(off)
        out.append((idx, access, code_off))
    return off, out

off, direct = read_methods(off, direct_methods)
off, virtual = read_methods(off, virtual_methods)

OPS = {
 0x00:('nop',1),0x0e:('return-void',1),0x1d:('monitor-enter',1),0x1e:('monitor-exit',1),
 0x26:('fill-array-data',3),0x27:('throw',1),0x28:('goto',1),
 0x01:('move',1),0x04:('move-wide',1),0x07:('move-object',1),
 0x0a:('move-result',1),0x0b:('move-result-wide',1),0x0c:('move-result-object',1),
 0x0d:('move-exception',1),0x0f:('return',1),0x10:('return-wide',1),0x11:('return-object',1),
 0x12:('const/4',1),0x21:('array-length',1),
 0x02:('move/from16',2),0x05:('move-wide/from16',2),0x08:('move-object/from16',2),
 0x03:('move/16',3),0x06:('move-wide/16',3),0x09:('move-object/16',3),
 0x13:('const/16',2),0x14:('const',3),0x15:('const/high16',2),
 0x16:('const-wide/16',2),0x17:('const-wide/32',3),0x18:('const-wide',5),
 0x19:('const-wide/high16',2),0x1a:('const-string',2),
 0x1b:('const-string/jumbo',3),0x1c:('const-class',2),0x1f:('check-cast',2),
 0x20:('instance-of',2),0x22:('new-instance',2),0x23:('new-array',2),
 0x24:('filled-new-array',3),0x25:('filled-new-array/range',3),
 0x29:('goto/16',2),0x2a:('goto/32',3),0x2b:('packed-switch',3),0x2c:('sparse-switch',3),
 0x2d:('cmpl-float',2),0x2e:('cmpg-float',2),0x2f:('cmpl-double',2),0x30:('cmpg-double',2),
 0x31:('cmp-long',2),
 0x32:('if-eq',2),0x33:('if-ne',2),0x34:('if-lt',2),0x35:('if-ge',2),0x36:('if-gt',2),0x37:('if-le',2),
 0x38:('if-eqz',2),0x39:('if-nez',2),0x3a:('if-ltz',2),0x3b:('if-gez',2),0x3c:('if-gtz',2),0x3d:('if-lez',2),
 0x44:('aget',2),0x45:('aget-wide',2),0x46:('aget-object',2),0x47:('aget-boolean',2),
 0x48:('aget-byte',2),0x49:('aget-char',2),0x4a:('aget-short',2),
 0x4b:('aput',2),0x4c:('aput-wide',2),0x4d:('aput-object',2),0x4e:('aput-boolean',2),
 0x4f:('aput-byte',2),0x50:('aput-char',2),0x51:('aput-short',2),
 0x52:('iget',2),0x53:('iget-wide',2),0x54:('iget-object',2),0x55:('iget-boolean',2),
 0x56:('iget-byte',2),0x57:('iget-char',2),0x58:('iget-short',2),
 0x59:('iput',2),0x5a:('iput-wide',2),0x5b:('iput-object',2),0x5c:('iput-boolean',2),
 0x5d:('iput-byte',2),0x5e:('iput-char',2),0x5f:('iput-short',2),
 0x60:('sget',2),0x61:('sget-wide',2),0x62:('sget-object',2),0x63:('sget-boolean',2),
 0x64:('sget-byte',2),0x65:('sget-char',2),0x66:('sget-short',2),
 0x67:('sput',2),0x68:('sput-wide',2),0x69:('sput-object',2),0x6a:('sput-boolean',2),
 0x6b:('sput-byte',2),0x6c:('sput-char',2),0x6d:('sput-short',2),
 0x6e:('invoke-virtual',3),0x6f:('invoke-super',3),0x70:('invoke-direct',3),
 0x71:('invoke-static',3),0x72:('invoke-interface',3),
 0x74:('invoke-virtual/range',3),0x75:('invoke-super/range',3),0x76:('invoke-direct/range',3),
 0x77:('invoke-static/range',3),0x78:('invoke-interface/range',3),
}
# 0x7b..0x8f unop (1), 0x90..0xaf binop 23x (2), 0xb0..0xcf binop/2addr (1),
# 0xd0..0xd7 binop/lit16 (2), 0xd8..0xe2 binop/lit8 (2)
for _op in range(0x7b, 0x90): OPS.setdefault(_op, ('unop', 1))
for _op in range(0x90, 0xb0): OPS.setdefault(_op, ('binop', 2))
for _op in range(0xb0, 0xd0): OPS.setdefault(_op, ('binop/2addr', 1))
for _op in range(0xd0, 0xd8): OPS.setdefault(_op, ('binop/lit16', 2))
for _op in range(0xd8, 0xe3): OPS.setdefault(_op, ('binop/lit8', 2))
for base_op in range(0x7b, 0x90):
    names = ['add-int','sub-int','mul-int','div-int','rem-int','and-int','or-int','xor-int',
             'shl-int','shr-int','ushr-int']
    fams = [('/2addr',2),('/lit16',2),('/lit8',3)]
    pass
BIN2ADDR = {0x90:'add-int',0x91:'sub-int',0x92:'mul-int',0x93:'div-int',0x94:'rem-int',
 0x95:'and-int',0x96:'or-int',0x97:'xor-int',0x98:'shl-int',0x99:'shr-int',0x9a:'ushr-int'}

for idx, access, code_off in direct + virtual:
    mcls, mname, mrt, mparams = get_method(idx)
    if mname != METHOD: continue
    print(f"method {mcls}.{mname} access=0x{access:04x} ret={mrt} params={mparams} code_off=0x{code_off:x}")
    if code_off == 0: continue
    registers, ins, outs, tries, debug, insns = struct.unpack_from('<HHHHII', b, code_off)
    base = code_off + 16
    print(f"registers={registers} ins={ins} outs={outs} insns={insns} units")
    i = 0
    while i < insns:
        if PC_LO is not None and (i < PC_LO or i > PC_HI):
            # still need to advance i by the correct width
            op = b[base + i*2]
            if op == 0x00:
                # nop / packed-switch payload / sparse-switch payload
                hi = b[base + i*2 + 1]
                if hi == 0x01:  # packed-switch payload
                    sz, = struct.unpack_from('<H', b, base + i*2 + 2)
                    w = (sz*4) + 4
                    i += (w + 1)//2
                    continue
                elif hi == 0x02:  # sparse-switch payload
                    sz, = struct.unpack_from('<H', b, base + i*2 + 2)
                    w = sz*4 + 2
                    i += (w + 1)//2
                    continue
                elif hi == 0x03:  # fill-array-data payload
                    ew, = struct.unpack_from('<H', b, base + i*2 + 2)
                    sz, = struct.unpack_from('<I', b, base + i*2 + 4)
                    w = sz*ew + 8
                    i += (w + 1)//2
                    continue
                w = 1
            else:
                w = OPS[op][1] if op in OPS else 1
            i += w
            continue
        op = b[base + i*2]
        unit, = struct.unpack_from('<H', b, base + i*2)
        note = ''
        if op == 0x00:
            hi = b[base + i*2 + 1]
            if hi == 0x01:
                sz, = struct.unpack_from('<H', b, base + i*2 + 2)
                ident, = struct.unpack_from('<H', b, base + i*2 + 4)
                print(f"  pc={i:#06x}: packed-switch-payload size={sz} first_key={ident}")
                i += (sz*4 + 4 + 1)//2
                continue
            if hi == 0x02:
                sz, = struct.unpack_from('<H', b, base + i*2 + 2)
                print(f"  pc={i:#06x}: sparse-switch-payload size={sz}")
                i += (sz*4 + 2 + 1)//2
                continue
            if hi == 0x03:
                ew, = struct.unpack_from('<H', b, base + i*2 + 2)
                sz, = struct.unpack_from('<I', b, base + i*2 + 4)
                print(f"  pc={i:#06x}: fill-array-data-payload elem_width={ew} size={sz}")
                i += (sz*ew + 8 + 1)//2
                continue
            print(f"  pc={i:#06x}: nop")
            i += 1
            continue
        name = OPS.get(op, (f"op_{op:#04x}", 1))[0]
        width = OPS.get(op, (None, 1))[1]
        A = (unit >> 8) & 0xf; AA = (unit >> 8) & 0xff
        B = (unit >> 12) & 0xf
        next16, = struct.unpack_from('<H', b, base + i*2 + 2) if width >= 2 else (0,)
        BBBB = next16 if width >= 2 else 0
        # 32-bit extension words (3-unit+ insns: word[2..3])
        w32, = struct.unpack_from('<I', b, base + i*2 + 4) if width >= 3 else (0,)
        w32s = w32 if width >= 3 else 0
        if op in (0x1a,):
            note = f" \"{get_string(BBBB)[:60]}\""
        elif op in (0x1c, 0x1f, 0x20, 0x22, 0x23, 0x24, 0x25):
            note = f" type={get_type(BBBB)}"
        elif 0x52 <= op <= 0x6d:
            fcls, ftyp, fname = get_field(BBBB)
            note = f" {fcls}.{fname}:{ftyp}"
        elif 0x60 <= op <= 0x6d:
            fcls, ftyp, fname = get_field(BBBB)
            note = f" {fcls}.{fname}:{ftyp}"
        elif 0x6e <= op <= 0x78:
            mcls2, mname2, mrt2, mpar2 = get_method(BBBB)
            args = ''
            if op <= 0x72:
                # 35c: A|G|op BBBB F|E|D|C — unit0 = A<<12|G<<8|op; unit2 holds FEDC
                third, = struct.unpack_from('<H', b, base + i*2 + 4)
                C = third & 0xf; D = (third>>4)&0xf; E = (third>>8)&0xf; F = (third>>12)&0xf
                G = (unit>>8)&0xf
                cnt = A
                regs = [C, D, E, F, G]
                args = ' v' + ', v'.join(str(r) for r in regs[:cnt]) if cnt else ''
            else:
                args = f" v{AA}..v{AA + max(len(mpar2),1) - 1}"
            note = f" {mcls2}.{mname2}:{mrt2}({','.join(mpar2)}){args}"
        elif op == 0x27:
            off8 = AA if AA < 0x80 else AA - 0x100
            note = f" -> pc={i + off8:#06x}"
        elif op == 0x28:
            # AOSP 0x28 = goto (10t): 8-bit signed offset in AA (high byte).
            off8 = AA if AA < 0x80 else AA - 0x100
            note = f" -> pc={i + off8:#06x}"
        elif op == 0x29:
            off16 = next16 if next16 < 0x8000 else next16 - 0x10000
            note = f" -> pc={i + off16:#06x}"
        elif op == 0x12:
            Bn = (unit >> 12) & 0xf
            if Bn >= 8: Bn -= 16
            note = f" v{A}={Bn}"
        elif op in (0x13, 0x16):
            s16, = struct.unpack_from('<h', b, base + i*2 + 2)
            note = f" v{AA}={s16}"
        elif op == 0x14:
            note = f" v{AA}={w32s:#x}"
        elif op in (0x32,0x33,0x34,0x35,0x36,0x37):
            off16 = next16
            if off16 >= 0x8000: off16 -= 0x10000
            note = f" v{A},v{B} -> pc={i + off16:#06x}"
        elif op in (0x38,0x39,0x3a,0x3b,0x3c,0x3d):
            # 21t: AA = register, offset in unit1 (signed)
            off16 = next16 if next16 < 0x8000 else next16 - 0x10000
            note = f" v{AA} -> pc={i + off16:#06x}"
        elif op in (0x2b, 0x2c):
            tgt, = struct.unpack_from('<i', b, base + i*2 + 4)
            note = f" table@pc={i + tgt:#06x}"
        elif op in (0x0a,0x0b,0x0c,0x0d,0x0f,0x10,0x11):
            note = f" v{AA}"
        elif op in (0x01,0x04,0x07,0x21):
            note = f" v{A}, v{B}"
        elif op in (0x02,0x05,0x08):
            note = f" v{AA}, v{next16}"
        elif op in (0x44,0x45,0x46,0x47,0x48,0x49,0x4a,0x4b,0x4c,0x4d,0x4e,0x4f,0x50,0x51):
            note = f" v{A}, v{B}, v{(next16>>0)&0xff}"
        elif op in (0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f):
            fcls, ftyp, fname = get_field(BBBB)
            note = f" v{A}, v{B} {fcls}.{fname}:{ftyp}"
        elif 0x90 <= op <= 0xaf:
            note = f" v{A}, v{B}, v{next16&0xff}"
        elif 0xb0 <= op <= 0xcf:
            note = f" v{A}, v{B}"
        elif 0xd0 <= op <= 0xd7:
            s16, = struct.unpack_from('<h', b, base + i*2 + 2)
            note = f" v{A}, v{B}, {s16}"
        elif 0xd8 <= op <= 0xe2:
            note = f" v{AA}, v{(next16>>0)&0xff}, {(next16>>8)&0xff}"
        marker = ' <<<' if PC_LO is not None and i == PC_LO else ''
        print(f"  pc={i:#06x}: {name}{note}{marker}")
        i += width
    break
