#!/usr/bin/env python3
"""w8_hexdump_method.py — raw-byte ground truth for one method's code item.
Usage: w8_hexdump_method.py <apk> <Lcls;> <method> [from_pc] [to_pc]
Dumps raw 16-bit code units with format-based decoding (full opcode size law).
"""
import sys, zipfile, struct

sys.path.insert(0, '/home/z/my-project/scripts')
from cont9_dexdump import Dex

# opcode -> (byte-size, format, name)
OPS = {}
def _r(a, b, size, fmt, name):  # range inclusive
    for o in range(a, b+1): OPS[o] = (size, fmt, name)
_r(0x00,0x00,2,'10x','nop'); _r(0x01,0x01,2,'12x','move')
_r(0x02,0x02,4,'22x','move/from16'); _r(0x03,0x03,6,'32x','move/16')
_r(0x04,0x04,2,'12x','move-wide'); _r(0x05,0x05,4,'22x','move-wide/from16'); _r(0x06,0x06,6,'32x','move-wide/16')
_r(0x07,0x07,2,'12x','move-object'); _r(0x08,0x08,4,'22x','move-object/from16'); _r(0x09,0x09,6,'32x','move-object/16')
_r(0x0a,0x0d,2,'11x','move-result*'); _r(0x0e,0x0e,2,'10x','return-void'); _r(0x0f,0x11,2,'11x','return*')
_r(0x12,0x12,2,'11n','const/4'); _r(0x13,0x13,4,'21s','const/16'); _r(0x14,0x14,6,'31i','const')
_r(0x15,0x15,4,'21h','const/high16'); _r(0x16,0x16,4,'21s','const-wide/16'); _r(0x17,0x17,6,'31i','const-wide/32')
_r(0x18,0x18,10,'51l','const-wide'); _r(0x19,0x19,4,'21h','const-wide/high16')
_r(0x1a,0x1a,4,'21c','const-string'); _r(0x1b,0x1b,6,'31c','const-string/jumbo'); _r(0x1c,0x1c,4,'21c','const-class')
_r(0x1d,0x1e,2,'11x','monitor*'); _r(0x1f,0x1f,4,'21c','check-cast'); _r(0x20,0x20,4,'22c','instance-of')
_r(0x21,0x21,2,'12x','array-length'); _r(0x22,0x22,4,'21c','new-instance'); _r(0x23,0x23,4,'22c','new-array')
_r(0x24,0x24,6,'35c','filled-new-array'); _r(0x25,0x25,6,'3rc','filled-new-array/range')
_r(0x26,0x26,6,'31t','fill-array-data'); _r(0x27,0x27,2,'11x','throw')
_r(0x28,0x28,2,'10t','goto'); _r(0x29,0x29,4,'20t','goto/16'); _r(0x2a,0x2a,10,'30t','goto/32')
_r(0x2b,0x2c,6,'31t','*-switch'); _r(0x2d,0x31,4,'23x','cmp*')
_r(0x32,0x37,4,'22t','if-*'); _r(0x38,0x3d,4,'21t','if-*z'); _r(0x3e,0x43,2,'10x','unused')
_r(0x44,0x51,4,'23x','a*get/put'); _r(0x52,0x5f,4,'22c','i*get/put')
_r(0x60,0x6d,4,'21c','s*get/put'); _r(0x6e,0x72,6,'35c','invoke-*')
_r(0x73,0x73,2,'10x','unused'); _r(0x74,0x78,6,'3rc','invoke-*/range')
_r(0x79,0x7a,2,'10x','unused'); _r(0x7b,0x8f,2,'12x','unary-op')
_r(0x90,0xaf,4,'23x','binop'); _r(0xb0,0xcf,2,'12x','binop/2addr')
_r(0xd0,0xe5,4,'22b','binop/lit8'); _r(0xe6,0xf9,4,'22s','binop/lit16')
_r(0xfa,0xfa,8,'45cc','invoke-polymorphic'); _r(0xfb,0xfb,8,'4rcc','invoke-polymorphic/range')
_r(0xfc,0xfd,4,'21c','const-method-*/'); _r(0xfe,0xff,2,'10x','unused')

BINOP_NAMES = {0x90:'add-int',0x91:'sub-int',0x92:'mul-int',0x93:'div-int',0x94:'rem-int',
 0x95:'and-int',0x96:'or-int',0x97:'xor-int',0x98:'shl-int',0x99:'shr-int',0x9a:'ushr-int',
 0x9b:'add-long',0x9c:'sub-long',0x9d:'mul-long',0x9e:'div-long',0x9f:'rem-long',
 0xa0:'and-long',0xa1:'or-long',0xa2:'xor-long',0xa3:'shl-long',0xa4:'shr-long',0xa5:'ushr-long',
 0xa6:'add-float',0xa7:'sub-float',0xa8:'mul-float',0xa9:'div-float',0xaa:'rem-float',
 0xab:'add-double',0xac:'sub-double',0xad:'mul-double',0xae:'div-double',0xaf:'rem-double',
 0xb0:'add-int/2addr',0xb1:'sub-int/2addr',0xb2:'mul-int/2addr',0xb3:'div-int/2addr',0xb4:'rem-int/2addr',
 0xb5:'and-int/2addr',0xb6:'or-int/2addr',0xb7:'xor-int/2addr',0xb8:'shl-int/2addr',0xb9:'shr-int/2addr',0xba:'ushr-int/2addr',
 0xbb:'add-long/2addr',0xbc:'sub-long/2addr',0xbd:'mul-long/2addr',0xbe:'div-long/2addr',0xbf:'rem-long/2addr',
 0xc0:'and-long/2addr',0xc1:'or-long/2addr',0xc2:'xor-long/2addr',0xc3:'shl-long/2addr',0xc4:'shr-long/2addr',0xc5:'ushr-long/2addr',
 0xd0:'add-int/lit8',0xd1:'sub-int/lit8',0xd2:'mul-int/lit8',0xd3:'div-int/lit8',0xd4:'rem-int/lit8',
 0xd5:'and-int/lit8',0xd6:'or-int/lit8',0xd7:'xor-int/lit8',0xd8:'shl-int/lit8',0xd9:'shr-int/lit8',0xda:'ushr-int/lit8',
 0xdb:'add-long/lit8',0xdc:'sub-long/lit8',0xdd:'mul-long/lit8',0xde:'div-long/lit8',0xdf:'rem-long/lit8',
 0xe0:'and-long/lit8',0xe1:'or-long/lit8',0xe2:'xor-long/lit8',0xe3:'shl-long/lit8',0xe4:'shr-long/lit8',0xe5:'ushr-long/lit8'}

def opname(op):
    if op in BINOP_NAMES: return BINOP_NAMES[op]
    return OPS[op][2] if op in OPS else f'op-{op:02x}'

apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
lo = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0
hi = int(sys.argv[5], 0) if len(sys.argv) > 5 else 1 << 30

z = zipfile.ZipFile(apk)
dex_bytes = z.read('classes.dex')
d = Dex(dex_bytes)

cdef = d.find_class(cls if cls.endswith(';') else cls)
if cdef is None:
    print('class not found:', cls); sys.exit(1)
info = d.class_methods(cdef)
target = None
for kind in ('direct', 'virtual'):
    for (mname, mdesc, acc, sz, code) in info[kind]:
        if mname == meth:
            target = (mname, mdesc, code); break
if not target:
    print('method not found; methods of', cls)
    for kind in ('direct', 'virtual'):
        for (mname, mdesc, acc, sz, code) in info[kind]:
            print(' ', kind, mname, mdesc)
    sys.exit(1)

code_off = target[2]
insns_size = struct.unpack_from('<I', dex_bytes, code_off + 12)[0]
insns_off = code_off + 16
print(f"{cls}.{meth}{target[1]} code_off=0x{code_off:x} insns_size=0x{insns_size:x} ({insns_size} units)")

def field_str(idx):
    try:
        cname, fname, ftype = d.field_ref(idx)
        return f"{cname}.{fname}:{ftype}"
    except Exception:
        return f"field@{idx}"

def method_str(idx):
    try:
        cname, mname, mdesc = d.method_ref(idx)
        return f"{cname}.{mname}{mdesc}"
    except Exception:
        return f"method@{idx}"

pc = 0
end = insns_size * 2
buf = dex_bytes
while pc < end:
    op = buf[insns_off + pc]
    size, fmt, _ = OPS.get(op, (2, '??', '?'))
    if pc >= lo and pc <= hi:
        detail = ''
        try:
            if fmt == '21t':
                reg = buf[insns_off+pc+1]
                off = struct.unpack_from('<h', buf, insns_off+pc+2)[0]
                detail = f"v{reg} -> 0x{pc + off*2:x}"
            elif fmt == '10t':
                off = struct.unpack_from('<b', buf, insns_off+pc+1)[0]
                detail = f"-> 0x{pc + off*2:x}"
            elif fmt == '20t':
                off = struct.unpack_from('<h', buf, insns_off+pc+2)[0]
                detail = f"-> 0x{pc + off*2:x}"
            elif fmt == '22t':
                b1 = buf[insns_off+pc+1]
                ra, rb = b1 & 0xf, (b1 >> 4) & 0xf
                off = struct.unpack_from('<h', buf, insns_off+pc+2)[0]
                detail = f"v{ra}, v{rb} -> 0x{pc + off*2:x}"
            elif fmt in ('21c',):
                reg = buf[insns_off+pc+1]
                idx = struct.unpack_from('<H', buf, insns_off+pc+2)[0]
                if op == 0x1a: detail = f"v{reg}, \"{d.string(idx)[:36]}\""
                elif op in (0x1c, 0x1f, 0x22, 0xfc, 0xfd): detail = f"v{reg}, {d.type_str(idx)}"
                else: detail = f"v{reg}, {field_str(idx)}"
            elif fmt == '31c':
                reg = buf[insns_off+pc+1]
                idx = struct.unpack_from('<I', buf, insns_off+pc+2)[0]
                detail = f"v{reg}, \"{d.string(idx)[:36]}\""
            elif fmt == '22c':
                nib = buf[insns_off+pc+1]
                ra, rb = nib & 0xf, (nib >> 4) & 0xf
                idx = struct.unpack_from('<H', buf, insns_off+pc+2)[0]
                if op == 0x20: detail = f"v{ra}, v{rb}, {d.type_str(idx)}"
                else: detail = f"v{ra}, v{rb}, {field_str(idx)}"
            elif fmt == '21s':
                reg = buf[insns_off+pc+1]
                val = struct.unpack_from('<h', buf, insns_off+pc+2)[0]
                detail = f"v{reg}, #{val} (0x{val & 0xffff:x})"
            elif fmt == '11n':
                b = buf[insns_off+pc+1]
                reg, val = b & 0xf, (b >> 4) & 0xf
                if val >= 8: val -= 16
                detail = f"v{reg}, #{val}"
            elif fmt == '11x':
                detail = f"v{buf[insns_off+pc+1]}"
            elif fmt == '12x':
                b = buf[insns_off+pc+1]
                if op in (0x12,):
                    reg, val = b & 0xf, (b >> 4) & 0xf
                    if val >= 8: val -= 16
                    detail = f"v{reg}, #{val}"
                else:
                    detail = f"v{b & 0xf}, v{(b >> 4) & 0xf}"
            elif fmt == '23x':
                detail = f"v{buf[insns_off+pc+1]}, v{buf[insns_off+pc+2]}, v{buf[insns_off+pc+3]}"
            elif fmt == '35c':
                A = (buf[insns_off+pc+1] >> 4) & 0xf
                G = buf[insns_off+pc+1] & 0xf
                idx = struct.unpack_from('<H', buf, insns_off+pc+2)[0]
                F = buf[insns_off+pc+4] & 0xf
                E = (buf[insns_off+pc+4] >> 4) & 0xf
                D = buf[insns_off+pc+5] & 0xf
                C = (buf[insns_off+pc+5] >> 4) & 0xf
                regs = [r for r in (C, D, E, F, G)][:A]
                detail = f"v{','.join(map(str,regs))}, {method_str(idx)}"
            elif fmt == '3rc':
                AA = buf[insns_off+pc+1]
                idx = struct.unpack_from('<H', buf, insns_off+pc+2)[0]
                CCCC = struct.unpack_from('<H', buf, insns_off+pc+4)[0]
                detail = f"v{CCCC}..v{CCCC+AA-1}, {method_str(idx)}"
            elif fmt == '31i':
                reg = buf[insns_off+pc+1]
                val = struct.unpack_from('<i', buf, insns_off+pc+2)[0]
                detail = f"v{reg}, #{val} (0x{val & 0xffffffff:x})"
            elif fmt == '22b':
                ra = buf[insns_off+pc+1]; rb = buf[insns_off+pc+2]
                val = struct.unpack_from('<b', buf, insns_off+pc+3)[0]
                detail = f"v{ra}, v{rb}, #{val}"
            elif fmt == '22s':
                nib = buf[insns_off+pc+1]
                ra, rb = nib & 0xf, (nib >> 4) & 0xf
                val = struct.unpack_from('<h', buf, insns_off+pc+2)[0]
                detail = f"v{ra}, v{rb}, #{val}"
            elif fmt == '22x':
                detail = f"v{buf[insns_off+pc+1]}, v{struct.unpack_from('<H', buf, insns_off+pc+2)[0]}"
            elif fmt == '21h':
                reg = buf[insns_off+pc+1]
                val = struct.unpack_from('<h', buf, insns_off+pc+2)[0]
                val = (val << 48) if op == 0x19 else (val << 16)
                detail = f"v{reg}, #0x{val:x}"
            elif fmt == '51l':
                reg = buf[insns_off+pc+1]
                val = struct.unpack_from('<q', buf, insns_off+pc+2)[0]
                detail = f"v{reg}, #0x{val & 0xffffffffffffffff:x}"
            elif fmt == '31t':
                reg = buf[insns_off+pc+1]
                off = struct.unpack_from('<i', buf, insns_off+pc+2)[0]
                detail = f"v{reg}, table@0x{pc + off*2:x}"
        except Exception as e:
            detail = f'<decode-err {e}>'
        print(f"  0x{pc:04x}: {opname(op):26s} {detail}")
    pc += size
