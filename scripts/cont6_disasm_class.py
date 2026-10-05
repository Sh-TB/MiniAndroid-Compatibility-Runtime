#!/usr/bin/env python3
"""cont6_disasm_class.py — dump all methods of one DEX class (optionally filter
by substring in disassembly body). Based on cont3_disasm_full.py.

Usage: cont6_disasm_class.py <apk> <Lcls;> [filter_substring] [--max-methods N]
"""
import sys, zipfile, struct

APK = sys.argv[1]
CLS = sys.argv[2]
FILT = sys.argv[3] if len(sys.argv) > 3 else None
MAXM = int(sys.argv[4]) if len(sys.argv) > 4 else 400

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

def get_method(i):
    cls, proto, name = struct.unpack_from('<HHI', b, method_ids_off + i*8)
    ps, rt, params = struct.unpack_from('<III', b, proto_ids_off + proto*12)
    if params == 0:
        plist = []
    else:
        size, = struct.unpack_from('<I', b, params)
        plist = [get_type(struct.unpack_from('<H', b, params + 4 + k*2)[0]) for k in range(size)]
    return get_type(cls), get_string(name), get_type(rt), plist

def get_field(i):
    cls, typ, name = struct.unpack_from('<HHI', b, field_ids_off + i*8)
    return get_type(cls), get_type(typ), get_string(name)

# OPCODE TABLE (subset adequate for operand-size stepping; from cont3 disasm)
FMT = {
 0x00:2,0x01:2,0x02:2,0x03:2,0x04:2,0x05:2,0x06:2,0x07:2,0x08:2,0x09:2,
 0x0a:2,0x0b:2,0x0c:2,0x0d:2,0x0e:2,0x0f:2,0x10:2,0x11:2,0x12:2,
 0x13:3,0x14:3,0x15:3,0x16:3,0x17:3,0x18:5,0x19:3,0x1a:3,
 0x1b:3,0x1c:3,0x1d:2,0x1e:2,0x1f:3,0x20:3,0x21:3,0x22:3,0x23:3,
 0x24:4,0x25:4,0x26:4,
 0x27:2,0x28:2,0x29:2,0x2a:2,0x2b:3,0x2c:3,
 0x2d:3,0x2e:3,0x2f:3,0x30:3,0x31:3,0x32:3,0x33:3,0x34:3,0x35:3,0x36:3,0x37:3,
 0x38:3,0x39:3,0x3a:3,0x3b:3,0x3c:3,0x3d:3,
 0x44:3,0x45:3,0x46:3,0x47:3,0x48:3,0x49:3,0x4a:3,0x4b:3,0x4c:3,0x4d:3,0x4e:3,
 0x4f:3,0x50:3,0x51:3,0x52:3,0x53:3,0x54:3,0x55:3,0x56:3,0x57:3,0x58:3,0x59:3,
 0x5a:3,0x5b:3,0x5c:3,0x5d:3,0x5e:3,0x5f:3,0x60:3,0x61:3,0x62:3,0x63:3,0x64:3,
 0x65:3,0x66:3,0x67:3,0x68:3,0x69:3,0x6a:3,0x6b:3,0x6c:3,0x6d:3,0x6e:4,0x6f:4,
 0x70:4,0x71:4,0x72:4,0x74:5,0x75:5,0x76:5,0x77:5,0x78:5,0x79:5,0x7a:5,
 0x7b:2,0x7c:2,0x7d:2,0x7e:2,0x7f:2,0x80:2,0x81:2,0x82:2,0x83:2,0x84:2,0x85:2,
 0x86:2,0x87:2,0x88:2,0x89:2,0x8a:2,0x8b:2,0x8c:2,0x8d:2,0x8e:2,0x8f:2,0x90:2,
 0x91:2,0x92:2,0x93:2,0x94:2,0x95:2,0x96:2,0x97:2,0x98:2,0x99:2,0x9a:2,0x9b:2,
 0x9c:2,0x9d:2,0x9e:2,0x9f:2,0xa0:2,0xa1:2,0xa2:2,0xa3:2,0xa4:2,0xa5:2,0xa6:2,
 0xa7:2,0xa8:2,0xa9:2,0xaa:2,0xab:2,0xac:2,0xad:2,0xae:2,0xaf:2,0xb0:2,0xb1:2,
 0xb2:2,0xb3:2,0xb4:2,0xb5:2,0xb6:2,0xb7:2,0xb8:2,0xb9:2,0xba:2,0xbb:2,0xbc:2,
 0xbd:2,0xbe:2,0xbf:2,0xc0:2,0xc1:2,0xc2:2,0xc3:2,0xc4:2,0xc5:2,0xc6:2,0xc7:2,
 0xc8:2,0xc9:2,0xca:2,0xcb:2,0xcc:2,0xcd:2,0xce:2,0xcf:2,
 0xd0:3,0xd1:3,0xd2:3,0xd3:3,0xd4:3,0xd5:3,0xd6:3,0xd7:3,0xd8:3,0xd9:3,0xda:3,
 0xdb:3,0xdc:3,0xdd:3,0xde:3,0xdf:3,0xe0:3,0xe1:3,0xe2:3,
 0xe3:3,0xe9:3,0xea:3,0xeb:3,0xec:3,0xed:3,0xef:3,0xf0:3,0xf2:5,0xf3:5,0xf5:3,
 0xf6:3,0xf7:3,0xf8:3,0xf9:3,0xfa:4,0xfb:4,0xfc:3,0xfd:3,0xfe:3,0xff:3,
}
# 45cc/4rcc/35mi/35c all handled by width below; simplified via high-byte map
def width(op, unit0):
    if 0x00 <= op <= 0x01: return 2
    if op in (0x2b, 0x2c): return 3
    if 0x2d <= op <= 0x31: return 3
    if 0x62 <= op <= 0x6d: return 3
    if op in (0x6e,0x6f,0x70,0x71,0x72,0x74,0x75,0x76,0x77,0x78): return 4 if op < 0x74 else 5
    if op in (0xfa,0xfb): return 4
    return FMT.get(op, 2)

OPNAMES = {
 0x00:'nop',0x01:'move',0x04:'move-wide',0x07:'move-object',0x0a:'move-result',
 0x0b:'move-result-wide',0x0c:'move-result-object',0x0d:'move-exception',
 0x0e:'return-void',0x0f:'return',0x10:'return-wide',0x11:'return-object',
 0x12:'const/4',0x13:'const/16',0x14:'const',0x15:'const/high16',0x16:'const-wide/16',
 0x17:'const-wide/32',0x18:'const-wide',0x19:'const-wide/high16',0x1a:'const-string',
 0x1b:'const-string/jumbo',0x1c:'const-class',0x1d:'monitor-enter',0x1e:'monitor-exit',
 0x1f:'check-cast',0x20:'instance-of',0x21:'array-length',0x22:'new-instance',
 0x23:'new-array',0x24:'filled-new-array',0x25:'filled-new-array/range',
 0x26:'fill-array-data',0x27:'throw',0x28:'goto',0x29:'goto/16',0x2a:'goto/32',
 0x2b:'packed-switch',0x2c:'sparse-switch',
 0x2d:'cmpl-float',0x2e:'cmpg-float',0x2f:'cmpl-double',0x30:'cmpg-double',
 0x31:'cmp-long',0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',
 0x37:'if-le',0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',
 0x3d:'if-lez',
 0x44:'aget',0x45:'aget-wide',0x46:'aget-object',0x47:'aget-boolean',0x48:'aget-byte',
 0x49:'aget-char',0x4a:'aget-short',0x4b:'aput',0x4c:'aput-wide',0x4d:'aput-object',
 0x4e:'aput-boolean',0x4f:'aput-byte',0x50:'aput-char',0x51:'aput-short',
 0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',0x56:'iget-byte',
 0x57:'iget-char',0x58:'iget-short',0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',
 0x5c:'iput-boolean',0x5d:'iput-byte',0x5e:'iput-char',0x5f:'iput-short',
 0x5a+0:'sget',0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x63:'sget-boolean',
 0x64:'sget-byte',0x65:'sget-char',0x66:'sget-short',0x67:'sput',0x68:'sput-wide',
 0x69:'sput-object',0x6a:'sput-boolean',0x6b:'sput-byte',0x6c:'sput-char',
 0x6d:'sput-short',
 0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',
 0x72:'invoke-interface',0x74:'invoke-virtual/range',0x75:'invoke-super/range',
 0x76:'invoke-direct/range',0x77:'invoke-static/range',0x78:'invoke-interface/range',
 0x7b:'int-to-long',0x7c:'int-to-float',0x7d:'int-to-double',0x7e:'long-to-int',
 0x7f:'long-to-float',0x80:'long-to-double',0x81:'float-to-int',0x82:'float-to-long',
 0x83:'float-to-double',0x84:'double-to-int',0x85:'double-to-long',0x86:'double-to-float',
 0x87:'int-to-byte',0x88:'int-to-char',0x89:'int-to-short',
 0x8a:'add-int',0x8b:'sub-int',0x8c:'mul-int',0x8d:'div-int',0x8e:'rem-int',
 0x8f:'and-int',0x90:'or-int',0x91:'xor-int',0x92:'shl-int',0x93:'shr-int',
 0x94:'ushr-int',0x95:'add-long',0x96:'sub-long',0x97:'mul-long',0x98:'div-long',
 0x99:'rem-long',0x9a:'and-long',0x9b:'or-long',0x9c:'xor-long',0x9d:'shl-long',
 0x9e:'shr-long',0x9f:'ushr-long',0xa0:'add-float',0xa1:'sub-float',0xa2:'mul-float',
 0xa3:'div-float',0xa4:'rem-float',0xa5:'add-double',0xa6:'sub-double',0xa7:'mul-double',
 0xa8:'div-double',0xa9:'rem-double',
 0xaa:'add-int/2addr',0xab:'sub-int/2addr',0xac:'mul-int/2addr',0xad:'div-int/2addr',
 0xae:'rem-int/2addr',0xaf:'and-int/2addr',0xb0:'or-int/2addr',0xb1:'xor-int/2addr',
 0xb2:'shl-int/2addr',0xb3:'shr-int/2addr',0xb4:'ushr-int/2addr',
 0xb5:'add-long/2addr',0xb6:'sub-long/2addr',0xb7:'mul-long/2addr',0xb8:'div-long/2addr',
 0xb9:'rem-long/2addr',0xba:'and-long/2addr',0xbb:'or-long/2addr',0xbc:'xor-long/2addr',
 0xbd:'shl-long/2addr',0xbe:'shr-long/2addr',0xbf:'ushr-long/2addr',
 0xc0:'add-float/2addr',0xc1:'sub-float/2addr',0xc2:'mul-float/2addr',
 0xc3:'div-float/2addr',0xc4:'rem-float/2addr',0xc5:'add-double/2addr',
 0xc6:'sub-double/2addr',0xc7:'mul-double/2addr',0xc8:'div-double/2addr',
 0xc9:'rem-double/2addr',
 0xca:'add-int/lit16',0xcb:'rsub-int',0xcc:'mul-int/lit16',0xcd:'div-int/lit16',
 0xce:'rem-int/lit16',0xcf:'and-int/lit16',0xd0:'or-int/lit16',0xd1:'xor-int/lit16',
 0xd2:'add-int/lit8',0xd3:'rsub-int/lit8',0xd4:'mul-int/lit8',0xd5:'div-int/lit8',
 0xd6:'rem-int/lit8',0xd7:'and-int/lit8',0xd8:'or-int/lit8',0xd9:'xor-int/lit8',
 0xda:'shl-int/lit8',0xdb:'shr-int/lit8',0xdc:'ushr-int/lit8',
 0xe3:' iget-quick?',0xe9:'invoke-polymorphic?',0xea:'invoke-polymorphic/range?',
 0xeb:'invoke-custom?',0xec:'invoke-custom/range?',0xed:'const-method-handle?',
 0xef:'const-method-type?',0xf2:'..',0xf3:'..',0xf5:'..',0xf6:'..',0xf7:'..',
 0xf8:'..',0xf9:'..',0xfa:'..',0xfb:'..',0xfc:'..',0xfd:'..',0xfe:'..',0xff:'..',
}

NAMES = {v: k for k, v in OPNAMES.items()}

def field_str(idx):
    cls, typ, name = get_field(idx)
    return f"{cls}.{name}:{typ}"

def method_str(idx):
    cls, name, ret, plist = get_method(idx)
    return f"{cls}.{name}:{ret}({','.join(plist)})"

def disasm(code_off, insns, regs, ins, outs):
    lines = []
    pc = 0
    while pc < insns:
        off = code_off + pc*2
        unit, = struct.unpack_from('<H', b, off)
        op = unit & 0xff
        name = OPNAMES.get(op, f"op-{op:#04x}")
        w = width(op, unit)
        txt = f"  pc={pc:#06x}({pc}): {name}"
        if op == 0x1a:  # const-string
            idx, = struct.unpack_from('<H', b, off+2)
            vAA = (unit >> 8) & 0xff
            txt += f" v{vAA}, \"{get_string(idx)}\""
        elif op == 0x1b:
            idx, = struct.unpack_from('<I', b, off+2)
            vAA = (unit >> 8) & 0xff
            txt += f" v{vAA}, \"{get_string(idx)}\""
        elif op in (0x22, 0x1c, 0x1f, 0x20, 0x23):  # new-instance/const-class/check-cast/instance-of/new-array
            idx, = struct.unpack_from('<H', b, off+2)
            txt += f" type={get_type(idx)}"
        elif 0x52 <= op <= 0x6d:  # field ops
            idx, = struct.unpack_from('<H', b, off+2)
            txt += f" {field_str(idx)}"
        elif 0x6e <= op <= 0x72 or op in (0x74,0x75,0x76,0x77,0x78):
            idx, = struct.unpack_from('<H', b, off+2)
            txt += f" {method_str(idx)}"
        elif op in (0x12,):  # const/4
            vB = (unit >> 12) & 0xf
            if vB >= 8: vB -= 16
            vA = (unit >> 8) & 0xf
            txt += f" v{vA}={vB}"
        elif op in (0x13,0x16,0x19):
            idx, = struct.unpack_from('<h', b, off+2)
            vAA = (unit >> 8) & 0xff
            txt += f" v{vAA}={idx}"
        elif op in (0x14,0x15,0x17,0x18):
            idx, = struct.unpack_from('<i', b, off+2)
            vAA = (unit >> 8) & 0xff
            txt += f" v{vAA}={idx}"
        elif 0x28 <= op <= 0x2a:  # goto
            if op == 0x28:
                vAA = (unit >> 8) & 0xff
                if vAA >= 128: vAA -= 256
                txt += f" -> pc={pc+vAA:#x}"
            elif op == 0x29:
                rel, = struct.unpack_from('<h', b, off+2)
                txt += f" -> pc={pc+rel:#x}"
            else:
                rel, = struct.unpack_from('<i', b, off+2)
                txt += f" -> pc={pc+rel:#x}"
        elif 0x32 <= op <= 0x3d:  # if vA, vB + rel
            rel, = struct.unpack_from('<h', b, off+2)
            txt += f" -> pc={pc+rel:#x}"
        lines.append(txt)
        pc += w
    return lines

# find class def
target = None
for i in range(class_defs_size):
    off = class_defs_off + i*32
    cls_idx, access, super_idx, _, _, _, cdo, _ = struct.unpack_from('<8I', b, off)
    if get_type(cls_idx) == CLS:
        target = (cls_idx, access, super_idx, cdo)
        break

if not target:
    print(f"class {CLS} NOT FOUND")
    sys.exit(1)

cls_idx, access, super_idx, cdo = target
print(f"class {CLS} access={access:#x} super={get_type(super_idx)} class_data_off={cdo:#x}")

if cdo == 0:
    sys.exit(0)

p = cdo
sfield_n, p = uleb(p)
ifield_n, p = uleb(p)
dm_n, p = uleb(p)
vm_n, p = uleb(p)
print(f"counts: sfields={sfield_n} ifields={ifield_n} dmethods={dm_n} vmethods={vm_n}")

# static fields first (DEX class_data order), then instance fields
idx = 0
for k in range(sfield_n):
    diff, p = uleb(p)
    access, p = uleb(p)
    idx += diff

# instance fields (idx_diff encoded)
fields = []
idx = 0
for k in range(ifield_n):
    diff, p = uleb(p)
    access, p = uleb(p)
    idx += diff
    fields.append(get_field(idx))
print(f"instance fields ({ifield_n}):")
for cls, typ, name in fields:
    print(f"  {CLS}.{name}:{typ}")

methods = []
mid = 0
for k in range(dm_n):
    diff, p = uleb(p)
    access, p = uleb(p)
    co, p = uleb(p)   # code_off uleb — REQUIRED third element
    mid += diff
    methods.append((mid, access, 'direct', co))
for k in range(vm_n):
    diff, p = uleb(p)
    access, p = uleb(p)
    co, p = uleb(p)   # code_off uleb
    mid += diff
    methods.append((mid, access, 'virtual', co))

count = 0
for mi, access, kind, co in methods:
    cls, name, ret, plist = get_method(mi)
    count += 1
    if count > MAXM: break
    print(f"method {CLS}.{name} {kind} access={access:#x} ret={ret} params={plist} code_off={co:#x}")

print("(use cont3_disasm_full.py <apk> <cls> <name> for bodies)")
