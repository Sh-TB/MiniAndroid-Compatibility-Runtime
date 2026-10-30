#!/usr/bin/env python3
"""CONT-11 TRAIN-1: disassemble Lt4;(AndroidComposeView).dispatchDraw fully.
Goal: find the AndroidCanvas-bridge construction (asComposeCanvas -> new
AndroidCanvas(android.graphics.Canvas)) and every branch around it.
Usage: cont11_train1_disasm.py [Lclass; [method]]
"""
import sys, zipfile, struct, io

APK = '/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apk'
TARGET_CLASS = sys.argv[1] if len(sys.argv) > 1 else 'Lt4;'
TARGET_METHOD = sys.argv[2] if len(sys.argv) > 2 else 'dispatchDraw'


def uleb(f):
    r = 0; sh = 0
    while True:
        b = f.read(1)[0]; r |= (b & 0x7f) << sh; sh += 7
        if not (b & 0x80): break
    return r


class Dex:
    def __init__(self, data):
        self.data = data
        (self.str_n, self.str_o) = struct.unpack_from('<II', data, 0x38)
        (self.type_n, self.type_o) = struct.unpack_from('<II', data, 0x40)
        (self.proto_n, self.proto_o) = struct.unpack_from('<II', data, 0x48)
        (self.fid_n, self.fid_o) = struct.unpack_from('<II', data, 0x50)
        (self.mid_n, self.mid_o) = struct.unpack_from('<II', data, 0x58)
        (self.cls_n, self.cls_o) = struct.unpack_from('<II', data, 0x60)

    def s(self, i):
        off = struct.unpack_from('<I', self.data, self.str_o + i*4)[0]
        f = io.BytesIO(self.data); f.seek(off)
        n = uleb(f); raw = f.read(n)
        return raw.decode('utf-8', 'replace')

    def t(self, i):
        return self.s(struct.unpack_from('<I', self.data, self.type_o + i*4)[0])

    def mid(self, i):
        cls_t, proto_t, name_i = struct.unpack_from('<HHI', self.data, self.mid_o + i*8)
        return self.t(cls_t), self.s(name_i), self.proto(idx=proto_t)

    def fid(self, i):
        cls_t, type_t, name_i = struct.unpack_from('<HHI', self.data, self.fid_o + i*8)
        return self.t(cls_t), self.s(name_i), self.t(type_t)

    def proto(self, idx):
        base = self.proto_o + idx * 12
        ret_t = struct.unpack_from('<H', self.data, base + 4)[0]
        po = struct.unpack_from('<I', self.data, base + 8)[0]
        if po == 0:
            params = []
        else:
            n = struct.unpack_from('<I', self.data, po)[0]
            params = [self.t(struct.unpack_from('<H', self.data, po + 4 + k*2)[0])
                      for k in range(n)]
        return f"({','.join(params)}){self.t(ret_t)}"

    def find_method(self, cls, name):
        for i in range(self.mid_n):
            c, n, p = self.mid(i)
            if c == cls and n == name:
                return i
        return None

    def class_data_loc(self, cls):
        for ci in range(self.cls_n):
            off = self.cls_o + ci*32
            (cidx, acc, sup, ifs, src, an, cdo, sv) = struct.unpack_from('<8I', self.data, off)
            if self.t(cidx) == cls:
                return cdo, sup
        return None, None

    def class_members(self, cls):
        """Return (super, [fields], [direct_methods], [virtual_methods]) with
        diff-correct member indices. Methods as (name, proto, code_off)."""
        cdo, sup = self.class_data_loc(cls)
        if not cdo:
            return sup, [], [], []
        f = io.BytesIO(self.data); f.seek(cdo)
        sf = uleb(f); inf = uleb(f); dm = uleb(f); vm = uleb(f)
        fields = []
        pos = 0
        for cnt in (sf, inf):  # each section's diffs restart from 0
            fidx = 0
            for _ in range(cnt):
                fidx += uleb(f); uleb(f)
                fields.append(self.fid(fidx))
        def methods(n):
            out = []; midx = 0
            for k in range(n):
                d = uleb(f)
                midx = d if k == 0 else midx + d  # diff from prev entry in this list
                acc2 = uleb(f); code_off = uleb(f)
                c, nm, p = self.mid(midx)
                out.append((nm, p, code_off))
            return out
        return sup, fields, methods(dm), methods(vm)

    def class_code(self, cls, mname):
        """Return (regs, insns_bytes) of cls.mname, or None."""
        for ci in range(self.cls_n):
            off = self.cls_o + ci*32
            (cidx, acc, sup, ifs, src, an, cdo, sv) = struct.unpack_from('<8I', self.data, off)
            if self.t(cidx) != cls or cdo == 0:
                continue
            f = io.BytesIO(self.data); f.seek(cdo)
            sf = uleb(f); inf = uleb(f); dm = uleb(f); vm = uleb(f)
            def skip_fields(n):
                for _ in range(n):
                    uleb(f); uleb(f)
            def skip_methods(n):
                for _ in range(n):
                    uleb(f); uleb(f); uleb(f)
            skip_fields(sf); skip_fields(inf)
            for _ in range(dm):
                midx_abs = uleb(f); uleb(f); code_off = uleb(f)  # direct: diff fresh
                if self.s(struct.unpack_from('<I', self.data, self.mid_o + midx_abs*8 + 4)[0]) != mname:
                    continue
                if code_off == 0:
                    return (0, b"", midx_abs)
                return self._read_code(code_off, midx_abs)
            for _ in range(vm):
                diff = uleb(f); acc2 = uleb(f); code_off = uleb(f)
                midx_abs = (midx_abs + diff) if _ else diff  # virtual: diff from prev in list
                if self.s(struct.unpack_from('<I', self.data, self.mid_o + midx_abs*8 + 4)[0]) != mname:
                    continue
                if code_off == 0:
                    return (0, b"", midx_abs)
                return self._read_code(code_off, midx_abs)
        return None

    def _read_code(self, code_off, midx_abs):
        # code_item: registers_size@0, ins_size@2, outs_size@4, tries_size@6,
        # debug_info_off@8, insns_size@12, insns@16
        regs = struct.unpack_from('<H', self.data, code_off + 0)[0]
        ins = struct.unpack_from('<H', self.data, code_off + 2)[0]
        insns_off = code_off + 16
        insns_sz = struct.unpack_from('<I', self.data, code_off + 12)[0]
        return (regs, self.data[insns_off:insns_off + insns_sz*2], midx_abs)



# opcode formats: (mnemonic, size_in_code_units, kind)
FMT = {}
def reg(name, size, kind):
    FMT[name] = (size, kind)

for op, nm in [(0x00,'nop'),(0x0e,'return-void'),(0x1d,'monitor-enter'),(0x1e,'monitor-exit'),(0x26,'throw'),(0x27,'goto')]:
    reg(nm,1,'none')
for op, nm in [(0x01,'move'),(0x04,'move-wide'),(0x07,'move-object'),(0x0a,'move-result'),(0x0b,'move-result-wide'),(0x0c,'move-result-object'),(0x0d,'move-exception'),(0x0f,'return'),(0x10,'return-wide'),(0x11,'return-object'),(0x12,'const/4'),(0x21,'array-length'),(0x1c,'const-class'),(0x1f,'check-cast'),(0x22,'new-instance'),(0x62,'sget'),(0x63,'sget-wide'),(0x64,'sget-object'),(0x65,'sget-boolean'),(0x66,'sget-byte'),(0x67,'sget-char'),(0x68,'sget-short'),(0x69,'sput'),(0x6a,'sput-wide'),(0x6b,'sput-object'),(0x6c,'sput-boolean'),(0x6d,'sput-byte'),(0x6e,'invoke-virtual'),(0x6f,'invoke-super'),(0x70,'invoke-direct'),(0x71,'invoke-static'),(0x72,'invoke-interface')]:
    pass
# sizes table (in 16-bit code units)
SIZES = {
 0x00:1,0x01:1,0x02:2,0x03:3,0x04:1,0x05:2,0x06:3,0x07:1,0x08:2,0x09:3,
 0x0a:1,0x0b:1,0x0c:1,0x0d:1,0x0e:1,0x0f:1,0x10:1,0x11:1,0x12:1,0x13:2,
 0x14:3,0x15:2,0x16:2,0x17:2,0x18:5,0x19:2,0x1a:2,0x1b:3,0x1c:2,0x1d:1,
 0x1e:1,0x1f:2,0x20:2,0x21:1,0x22:2,0x23:2,0x24:3,0x25:3,0x26:1,0x27:1,
 0x28:1,0x29:2,0x2a:3,0x2b:3,0x2c:3,
 0x2d:2,0x2e:2,0x2f:2,0x30:2,0x31:2,0x32:2,0x33:2,0x34:2,0x35:2,0x36:2,
 0x37:2,0x38:2,0x39:2,0x3a:2,0x3b:2,0x3c:2,0x3d:2,
 0x44:2,0x45:2,0x46:2,0x47:2,0x48:2,0x49:2,0x4a:2,0x4b:2,0x4c:2,0x4d:2,
 0x4e:2,0x4f:2,0x50:2,0x51:2,
 0x52:2,0x53:2,0x54:2,0x55:2,0x56:2,0x57:2,0x58:2,0x59:2,0x5a:2,0x5b:2,
 0x5c:2,0x5d:2,0x5e:2,0x5f:2,0x60:2,0x61:2,0x62:2,0x63:2,0x64:2,0x65:2,
 0x66:2,0x67:2,0x68:2,0x69:2,0x6a:2,0x6b:2,0x6c:2,0x6d:2,
 0x6e:3,0x6f:3,0x70:3,0x71:3,0x72:3,0x74:3,0x75:3,0x76:3,0x77:3,0x78:3,
 0x74:3,
 0x79:2,0x7a:3,
 0xd0:2,0xd1:2,0xd2:2,0xd3:2,0xd4:2,0xd5:2,0xd6:2,0xd7:2,
 0xd8:2,0xd9:2,0xda:2,0xdb:2,0xdc:2,0xdd:2,0xde:2,0xdf:2,
 0xe0:2,0xe1:2,0xe2:2,0xe3:2,0xe4:2,0xe5:2,0xe6:2,0xe7:2,
 0xe8:2,0xe9:2,0xea:2,0xeb:2,0xec:2,0xed:2,0xee:2,0xef:2,
 0xf0:2,0xf1:2,0xf2:2,0xf3:2,0xf4:2,0xf5:2,0xf6:2,0xf7:2,
 0xf8:2,0xf9:2,0xfa:2,0xfb:2,0xfc:2,0xfd:2,0xfe:2,0xff:2,
}
NAMES = {
 0x01:'move',0x02:'move/from16',0x03:'move/16',0x04:'move-wide',0x05:'move-wide/from16',
 0x06:'move-wide/16',0x07:'move-object',0x08:'move-object/from16',0x09:'move-object/16',
 0x0a:'move-result',0x0b:'move-result-wide',0x0c:'move-result-object',0x0d:'move-exception',
 0x0e:'return-void',0x0f:'return',0x10:'return-wide',0x11:'return-object',
 0x12:'const/4',0x13:'const/16',0x14:'const',0x15:'const/high16',0x16:'const-wide/16',
 0x17:'const-wide/32',0x18:'const-wide',0x19:'const-wide/high16',0x1a:'const-string',
 0x1b:'const-string/jumbo',0x1c:'const-class',0x1f:'check-cast',0x20:'instance-of',
 0x21:'array-length',0x22:'new-instance',0x23:'new-array',0x24:'filled-new-array',
 0x25:'filled-new-array/range',0x26:'throw',0x27:'goto',0x28:'goto/16',0x29:'goto/32',
 0x2a:'packed-switch',0x2b:'sparse-switch',
 0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',
 0x72:'invoke-interface',0x74:'invoke-virtual/range',0x75:'invoke-super/range',
 0x76:'invoke-direct/range',0x77:'invoke-static/range',0x78:'invoke-interface/range',
}
for op in list(range(0x2d,0x3e)) + list(range(0x44,0x52)) + list(range(0x52,0x62)) + list(range(0x90,0xb0)) + list(range(0xd0,0xe0)):
    if op not in NAMES: NAMES[op] = f'op-0x{op:02x}'
for op in range(0x52,0x62): pass
BINOP2 = {0x90:'add-int',0x91:'sub-int',0x92:'mul-int',0x93:'div-int',0x94:'rem-int',
 0x95:'and-int',0x96:'or-int',0x97:'xor-int',0x98:'shl-int',0x99:'shr-int',0x9a:'ushr-int',
 0x9b:'add-long',0x9c:'sub-long',0x9d:'mul-long',0x9e:'div-long',0x9f:'rem-long',
 0xa0:'and-long',0xa1:'or-long',0xa2:'xor-long',0xa3:'shl-long',0xa4:'shr-long',0xa5:'ushr-long',
 0xa6:'add-float',0xa7:'sub-float',0xa8:'mul-float',0xa9:'div-float',0xaa:'rem-float',
 0xab:'add-double',0xac:'sub-double',0xad:'mul-double',0xae:'div-double',0xaf:'rem-double',
 0xb0:'add-int/2addr',0xb1:'sub-int/2addr',0xb2:'mul-int/2addr',0xb3:'div-int/2addr',0xb4:'rem-int/2addr',
 0xb5:'and-int/2addr',0xb6:'or-int/2addr',0xb7:'xor-int/2addr',0xb8:'shl-int/2addr',0xb9:'shr-int/2addr',0xba:'ushr-int/2addr',
 0xbb:'add-long/2addr',0xbc:'sub-long/2addr',0xbd:'mul-long/2addr',0xbe:'div-long/2addr',0xbf:'rem-long/2addr',
 0xc0:'and-long/2addr',0xc1:'or-long/2addr',0xc2:'xor-long/2addr',0xc3:'shl-long/2addr',0xc4:'shr-long/2addr',0xc5:'ushr-long/2addr',
 0xc6:'add-float/2addr',0xc7:'sub-float/2addr',0xc8:'mul-float/2addr',0xc9:'div-float/2addr',0xca:'rem-float/2addr',
 0xcb:'add-double/2addr',0xcc:'sub-double/2addr',0xcd:'mul-double/2addr',0xce:'div-double/2addr',0xcf:'rem-double/2addr',
 0xd0:'add-int/lit16',0xd1:'rsub-int',0xd2:'mul-int/lit16',0xd3:'div-int/lit16',0xd4:'rem-int/lit16',
 0xd5:'and-int/lit16',0xd6:'or-int/lit16',0xd7:'xor-int/lit16',
 0xd8:'add-int/lit8',0xd9:'rsub-int/lit8',0xda:'mul-int/lit8',0xdb:'div-int/lit8',0xdc:'rem-int/lit8',
 0xdd:'and-int/lit8',0xde:'or-int/lit8',0xdf:'xor-int/lit8',0xe0:'shl-int/lit8',0xe1:'shr-int/lit8',0xe2:'ushr-int/lit8'}
NAMES.update(BINOP2)
AGET = {0x44:'aget',0x45:'aget-wide',0x46:'aget-object',0x47:'aget-boolean',0x48:'aget-byte',
 0x49:'aget-char',0x4a:'aget-short',0x4b:'aput',0x4c:'aput-wide',0x4d:'aput-object',
 0x4e:'aput-boolean',0x4f:'aput-byte',0x50:'aput-char',0x51:'aput-short'}
NAMES.update(AGET)
CMP = {0x2d:'cmpl-float',0x2e:'cmpg-float',0x2f:'cmpl-double',0x30:'cmpg-double',0x31:'cmp-long'}
NAMES.update(CMP)
CAST = {0x80:'int-to-long',0x81:'int-to-float',0x82:'int-to-double',0x83:'long-to-int',0x84:'long-to-float',
 0x85:'long-to-double',0x86:'float-to-int',0x87:'float-to-long',0x88:'float-to-double',
 0x89:'double-to-int',0x8a:'double-to-long',0x8b:'double-to-float',0x8c:'int-to-byte',0x8d:'int-to-char',0x8e:'int-to-short'}
NAMES.update(CAST)



def disasm(dx, cls, mname):
    got = dx.class_code(cls, mname)
    if not got:
        print(f'METHOD NOT FOUND: {cls}.{mname}'); return
    regs, ins, midx = got
    if not ins:
        print(f'{cls}.{mname}: abstract/native'); return
    proto = dx.mid(midx)[2]
    print(f'=== {cls}.{mname}{proto} regs={regs} insns={len(ins)//2} ===')
    u16 = lambda off: struct.unpack_from('<H', ins, off*2)[0]
    i32 = lambda off: struct.unpack_from('<i', ins, off*2)[0]
    pc = 0
    while pc < len(ins)//2:
        op = ins[pc*2] & 0xFF
        size = SIZES.get(op, 1)
        name = NAMES.get(op, f'op-0x{op:02x}')
        extra = ''
        aa = ins[pc*2+1]
        if op in (0x1a,):
            si = u16(pc+1); extra = f'"{dx.s(si)[:40]}"'
        elif op in (0x1b,):
            si = i32(pc+1); extra = f'"{dx.s(si)[:40]}"'
        elif op in (0x22,0x1c,0x20,0x23):
            ti = u16(pc+1); extra = dx.t(ti)
        elif op in (0x6e,0x6f,0x70,0x71,0x72):
            mi = u16(pc+1)
            c, n, p = dx.mid(mi)
            extra = f'{c}.{n}{p}'
        elif op in (0x74,0x75,0x76,0x77,0x78):
            mi = u16(pc+1)
            c, n, p = dx.mid(mi)
            extra = f'{c}.{n}{p} [range]'
        elif op in (0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f,0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d):
            fi = u16(pc+1)
            c, n, ty = dx.fid(fi)
            extra = f'{c}.{n}:{ty}'
        elif op == 0x26:
            pass
        elif op in (0x27,):
            extra = f'-> PC={pc + 1 + aa}'
        elif op == 0x28:
            d = struct.unpack_from('<h', ins, (pc+1)*2)[0]
            extra = f'-> PC={pc + 1 + d}'
        elif op == 0x29:
            d = i32(pc+1)
            extra = f'-> PC={pc + 1 + d}'
        elif 0x2d <= op <= 0x3d:
            d = struct.unpack_from('<h', ins, (pc+1)*2)[0]
            extra = f'-> PC={pc + 1 + d}'
        print(f'  {pc:04d} {name} {extra}')
        pc += size
    print(f'  END pc={pc}')


z = zipfile.ZipFile(APK)
for dn in sorted(n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')):
    data = z.read(dn)
    dx = Dex(data)
    print(f'--- {dn} ---')
    disasm(dx, TARGET_CLASS, TARGET_METHOD)
