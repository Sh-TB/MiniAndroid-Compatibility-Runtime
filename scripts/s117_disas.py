#!/usr/bin/env python3
"""S117 — full-opcode Dalvik disassembler window for the official Telegram APK.
Usage: s117_disas.py <Lclass;> <method> [start_pc] [end_pc]"""
import sys, struct, zipfile

APK = '/home/z/my-project/upload/tg/telegram_official.apk'
W = [1]*256
def _setw(a, b_, w):
    for o in range(a, b_+1): W[o] = w
W[0x12]=1; W[0x13]=2; W[0x14]=3; W[0x15]=2; W[0x16]=2; W[0x17]=3; W[0x18]=5; W[0x19]=2
W[0x1a]=2; W[0x1b]=3; W[0x1c]=2; W[0x1d]=1; W[0x1e]=1; W[0x1f]=2; W[0x20]=2; W[0x21]=1
W[0x22]=2; W[0x23]=2; W[0x24]=3; W[0x25]=3; W[0x26]=3; W[0x27]=1; W[0x28]=1; W[0x29]=2
W[0x2a]=3; W[0x2b]=3; W[0x2c]=3
_setw(0x2d,0x31,2); _setw(0x32,0x37,2); _setw(0x38,0x3d,2); _setw(0x44,0x51,2)
_setw(0x52,0x6d,2); _setw(0x6e,0x72,3); _setw(0x74,0x78,3); _setw(0x7b,0x8f,1)
_setw(0x90,0xaf,2); _setw(0xb0,0xcf,1); _setw(0xd0,0xd7,2); _setw(0xd8,0xe2,2)

NAMES = {
 0x00:'nop',0x01:'move',0x02:'move/from16',0x03:'move/16',0x04:'move-wide',0x05:'move-wide/from16',
 0x06:'move-wide/16',0x07:'move-object',0x08:'move-object/from16',0x09:'move-object/16',
 0x0a:'move-result',0x0b:'move-result-wide',0x0c:'move-result-object',0x0d:'move-exception',
 0x0e:'return-void',0x0f:'return',0x10:'return-wide',0x11:'return-object',0x12:'const/4',
 0x13:'const/16',0x14:'const',0x15:'const/high16',0x16:'const-wide/16',0x17:'const-wide/32',
 0x18:'const-wide',0x19:'const-wide/high16',0x1a:'const-string',0x1b:'const-string/jumbo',
 0x1c:'const-class',0x1d:'monitor-enter',0x1e:'monitor-exit',0x1f:'check-cast',0x20:'instance-of',
 0x21:'array-length',0x22:'new-instance',0x23:'new-array',0x24:'filled-new-array',0x25:'filled-new-array/range',
 0x26:'fill-array-data',0x27:'throw',0x28:'goto',0x29:'goto/16',0x2a:'goto/32',0x2b:'packed-switch',
 0x2c:'sparse-switch',0x2d:'cmpl-float',0x2e:'cmpg-float',0x2f:'cmpl-double',0x30:'cmpg-double',
 0x31:'cmp-long',0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',0x37:'if-le',
 0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez',
 0x44:'aget',0x45:'aget-wide',0x46:'aget-object',0x47:'aget-boolean',0x48:'aget-byte',0x49:'aget-char',
 0x4a:'aget-short',0x4b:'aput',0x4c:'aput-wide',0x4d:'aput-object',0x4e:'aput-boolean',0x4f:'aput-byte',
 0x50:'aput-char',0x51:'aput-short',0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',
 0x56:'iget-byte',0x57:'iget-char',0x58:'iget-short',0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',
 0x5c:'iput-boolean',0x5d:'iput-byte',0x5e:'iput-char',0x5f:'iput-short',0x60:'sget',0x61:'sget-wide',
 0x62:'sget-object',0x63:'sget-boolean',0x64:'sget-byte',0x65:'sget-char',0x66:'sget-short',0x67:'sput',
 0x68:'sput-wide',0x69:'sput-object',0x6a:'sput-boolean',0x6b:'sput-byte',0x6c:'sput-char',0x6d:'sput-short',
 0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface',
 0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',0x77:'invoke-static/range',
 0x78:'invoke-interface/range',0x7b:'neg-int',0x7c:'not-int',0x7d:'neg-long',0x7e:'not-long',
 0x7f:'neg-float',0x80:'neg-double',0x81:'int-to-long',0x82:'int-to-float',0x83:'int-to-double',
 0x84:'long-to-int',0x85:'long-to-float',0x86:'long-to-double',0x87:'float-to-int',0x88:'float-to-long',
 0x89:'float-to-double',0x8a:'double-to-int',0x8b:'double-to-long',0x8c:'double-to-float',
 0x8d:'int-to-byte',0x8e:'int-to-char',0x8f:'int-to-short',
}
BINOPS = ['add','sub','mul','div','rem','and','or','xor','shl','shr','ushr']
for i, nm in enumerate(BINOPS):
    NAMES[0x90+i]=f'{nm}-int'; NAMES[0x9b+i]=f'{nm}-long'
    NAMES[0xa6+i]=f'{nm}-float'; NAMES[0xab+i]=f'{nm}-double'
    NAMES[0xb0+i]=f'{nm}-int/2addr'; NAMES[0xbb+i]=f'{nm}-long/2addr'
    NAMES[0xc6+i]=f'{nm}-float/2addr'; NAMES[0xcb+i]=f'{nm}-double/2addr'
for i, nm in enumerate(BINOPS[:7]):
    NAMES[0xd0+i]=f'{nm}-int/lit16'
for i, nm in enumerate(BINOPS):
    NAMES[0xd8+i]=f'{nm}-int/lit8'

def uleb128(b, off):
    r, s = 0, 0
    while True:
        x = b[off]; off += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, off

class Dex:
    def __init__(self, b):
        self.b = b
        (self.str_ids_size, self.str_ids_off) = struct.unpack_from('<II', b, 0x38)
        (self.type_ids_size, self.type_ids_off) = struct.unpack_from('<II', b, 0x40)
        (self.field_ids_size, self.field_ids_off) = struct.unpack_from('<II', b, 0x50)
        (self.method_ids_size, self.method_ids_off) = struct.unpack_from('<II', b, 0x58)
        (self.class_defs_size, self.class_defs_off) = struct.unpack_from('<II', b, 0x60)
    def str_at(self, idx):
        off = struct.unpack_from('<I', self.b, self.str_ids_off + idx*4)[0]
        n, off = uleb128(self.b, off)
        end = off
        while self.b[end] != 0: end += 1
        return self.b[off:end].decode('utf-8', 'replace')
    def type_at(self, idx):
        si = struct.unpack_from('<I', self.b, self.type_ids_off + idx*4)[0]
        return self.str_at(si)
    def method_at(self, idx):
        cls_idx, proto_idx, name_idx = struct.unpack_from('<HHI', self.b, self.method_ids_off + idx*8)
        return self.type_at(cls_idx), self.str_at(name_idx)
    def field_at(self, idx):
        cls_idx, type_idx, name_idx = struct.unpack_from('<HHI', self.b, self.field_ids_off + idx*8)
        return self.type_at(cls_idx), self.type_at(type_idx), self.str_at(name_idx)
    def find_class(self, type_desc):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + i*32
            class_idx, = struct.unpack_from('<I', self.b, off)
            if self.type_at(class_idx) == type_desc: return off
        return None
    def class_methods(self, off):
        b = self.b
        class_data_off, = struct.unpack_from('<I', b, off + 24)
        if class_data_off == 0: return []
        p = class_data_off
        static_f, p = uleb128(b, p); inst_f, p = uleb128(b, p)
        direct_m, p = uleb128(b, p); virtual_m, p = uleb128(b, p)
        out = []
        for _ in range(static_f + inst_f):
            _, p = uleb128(b, p); _, p = uleb128(b, p)
        for kind, count in (('direct', direct_m), ('virtual', virtual_m)):
            midx = 0
            for _ in range(count):
                d, p = uleb128(b, p); midx += d
                _, p = uleb128(b, p)
                code_off, p = uleb128(b, p)
                cn, mn = self.method_at(midx)
                out.append((kind, cn, mn, code_off))
        return out
    def code_units(self, code_off):
        b = self.b
        if code_off == 0: return []
        insns_size, = struct.unpack_from('<I', b, code_off + 12)
        insns_off = code_off + 16
        return list(struct.unpack_from('<%dH' % insns_size, b, insns_off))

def disasm(d, units, lo, hi):
    i = 0
    while i < len(units):
        op = units[i] & 0xff
        w = W[op] or 1
        if op == 0x00:
            hi_n = units[i] >> 8
            if hi_n == 0x01:
                sz = units[i+1]; i += 4 + sz; continue
            elif hi_n == 0x02:
                sz = units[i+1]; i += 2 + 4*sz; continue
            i += 1; continue
        if lo <= i <= hi:
            u0 = units[i]
            u1 = units[i+1] if i+1 < len(units) else 0
            u2 = units[i+2] if i+2 < len(units) else 0
            name = NAMES.get(op, f'op_{op:02x}')
            s = f'  +{i:05d} {name}'
            aa = (u0 >> 8) & 0xff
            try:
                if op == 0x12:
                    lit = (aa >> 4) & 0xf
                    if lit >= 8: lit -= 16
                    s += f' v{aa & 0xf}, #{lit}'
                elif op == 0x1a: s += f' v{aa}, string@{u1} "{d.str_at(u1)[:60]}"'
                elif op == 0x1b: s += f' v{aa}, string@{u1|(u2<<16)}'
                elif op in (0x1c,0x1f,0x22): s += f' v{aa}, type {d.type_at(u1)}'
                elif op == 0x23: s += f' v{aa&0xf}, v{(u0>>12)&0xf}, type {d.type_at(u1)}'
                elif 0x44 <= op <= 0x51: s += f' v{aa}, v{u1&0xff}, v{(u1>>8)&0xff}'
                elif 0x52 <= op <= 0x5f:
                    cc, tc, fc = d.field_at(u1); s += f' v{aa&0xf}, v{(u0>>12)&0xf}, {cc}.{fc}:{tc[0]}'
                elif 0x60 <= op <= 0x6d:
                    cc, tc, fc = d.field_at(u1); s += f' v{aa}, {cc}.{fc}:{tc[0]}'
                elif op in (0x6e,0x6f,0x70,0x71,0x72):
                    cn, mn = d.method_at(u1)
                    regs = []
                    fd = u2; regs = [fd&0xf,(fd>>4)&0xf,(fd>>8)&0xf,(fd>>12)&0xf, aa&0xf][:aa>>4]
                    s += f' {{{", ".join(f"v{r}" for r in regs)}}}, {cn}.{mn}'
                elif op in (0x74,0x75,0x76,0x77,0x78):
                    cn, mn = d.method_at(u2); s += f' {{v{u1}..v{u1+((aa>>4)-1)}}}, {cn}.{mn}'
                elif op in (0x32,0x33,0x34,0x35,0x36,0x37): s += f' v{(u0>>12)&0xf}, v{aa&0xf}, ->{u1:+d} (to {i+ (u1 if u1<0x8000 else u1-0x10000)})'
                elif op in (0x38,0x39,0x3a,0x3b,0x3c,0x3d): s += f' v{aa}, ->{u1:+d} (to {i + (u1 if u1<0x8000 else u1-0x10000)})'
                elif op == 0x28: s += f' ->{(aa if aa<0x80 else aa-0x100):+d} (to {i+(aa if aa<0x80 else aa-0x100)})'
                elif op == 0x29: s += f' ->{u1:+d} (to {i + (u1 if u1<0x8000 else u1-0x10000)})'
                elif op == 0x2a: off32 = u1 | (u2<<16); s += f' ->{off32:+d} (to {i+off32})'
                elif op == 0x21: s += f' v{aa&0xf}, v{(u0>>12)&0xf}'
                elif op in (0x01,0x04,0x07): s += f' v{aa&0xf}, v{(u0>>12)&0xf}'
                elif 0x7b <= op <= 0x8f: s += f' v{aa&0xf}, v{(u0>>12)&0xf}'
                elif 0xb0 <= op <= 0xcf: s += f' v{aa&0xf}, v{(u0>>12)&0xf}'
                elif op in (0x0a,0x0b,0x0c,0x0d): s += f' v{aa}'
                elif op in (0x0e,): s += ''
                elif op in (0x0f,0x10,0x11,0x27,0x1d,0x1e): s += f' v{aa}'
                elif op == 0x13: s += f' v{aa}, #{struct.unpack("<h", struct.pack("<H", u1))[0]}'
                elif op == 0x14: s += f' v{aa}, #{struct.unpack("<i", struct.pack("<HH", u1, u2))[0]}'
                elif op == 0x15: s += f' v{aa}, #{struct.unpack("<h", struct.pack("<H", u1))[0]}<<16'
                elif 0xd8 <= op <= 0xe2: s += f' v{aa}, v{u1&0xff}, #{struct.unpack("<b", struct.pack("<B",(u1>>8)&0xff))[0]}'
                elif 0xd0 <= op <= 0xd7: s += f' v{aa&0xf}, v{(u0>>12)&0xf}, #{struct.unpack("<h", struct.pack("<H", u1))[0]}'
                elif 0x90 <= op <= 0xaf: s += f' v{aa}, v{u1&0xff}, v{(u1>>8)&0xff}'
                elif 0x2d <= op <= 0x31: s += f' v{aa}, v{u1&0xff}, v{(u1>>8)&0xff}'
                elif op in (0x24,): s += f' nargs={aa>>4}'
                elif op in (0x26,): s += f' v{aa&0xf}, payload@+{u1}'
            except Exception as e:
                s += f' <{e}>'
            print(s)
        i += w

def main():
    cls, meth = sys.argv[1], sys.argv[2]
    lo = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    hi = int(sys.argv[4]) if len(sys.argv) > 4 else 10**9
    z = zipfile.ZipFile(APK)
    for dn in sorted(n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')):
        d = Dex(z.read(dn))
        off = d.find_class(cls)
        if off is None: continue
        for kind, cn, mn, code_off in d.class_methods(off):
            if mn.split('(')[0] != meth: continue
            units = d.code_units(code_off)
            if not units: continue
            regs, ins, outs = struct.unpack_from('<HHH', d.b, code_off)[:3]
            print(f'=== {dn} {cls}.{mn} [{kind}] units={len(units)} regs={regs} ins={ins}')
            disasm(d, units, lo, hi)
            print()

if __name__ == '__main__':
    main()

