#!/usr/bin/env python3
"""cont67_disasm.py — parametric DEX method disassembler (cont66 recipe).
Usage: cont67_disasm.py <apk> <class-descriptor> <method-name-or-all> [dex-name]
"""
import zipfile, struct, sys

APK = sys.argv[1]
CLS = sys.argv[2]
METH = sys.argv[3] if len(sys.argv) > 3 else 'onCreate'

OPCODES = {
0x00:'nop',0x01:'move',0x02:'move/from16',0x04:'move-wide',0x05:'move-wide/16',
0x07:'move-object',0x08:'move-object/from16',0x0a:'move-result',0x0b:'move-result-wide',
0x0c:'move-result-object',0x0d:'move-exception',0x0e:'return-void',0x0f:'return',
0x10:'return-wide',0x11:'return-object',0x12:'const/4',0x13:'const/16',0x14:'const',
0x15:'const/high16',0x16:'const-wide/16',0x17:'const-wide/32',0x18:'const-wide',
0x19:'const-wide/high16',0x1a:'const-string',0x1b:'const-string/jumbo',0x1c:'const-class',
0x1d:'monitor-enter',0x1e:'monitor-exit',0x1f:'check-cast',0x20:'instance-of',
0x21:'array-length',0x22:'new-instance',0x23:'new-array',0x24:'filled-new-array',
0x25:'filled-new-array/range',0x26:'fill-array-data',0x27:'throw',0x28:'goto',
0x29:'goto/16',0x2a:'goto/32',0x2b:'packed-switch',0x2c:'sparse-switch',
0x2d:'cmpl-float',0x2e:'cmpg-float',0x2f:'cmpl-double',0x30:'cmpg-double',0x31:'cmp-long',
0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',0x37:'if-le',
0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez',
0x3e-0x43:'unused',
0x44:'aget',0x45:'aget-wide',0x46:'aget-object',0x47:'aget-boolean',0x48:'aget-byte',
0x49:'aget-char',0x4a:'aget-short',0x4b:'aput',0x4c:'aput-wide',0x4d:'aput-object',
0x4e:'aput-boolean',0x4f:'aput-byte',0x50:'aput-char',0x51:'aput-short',
0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',0x56:'iget-byte',
0x57:'iget-char',0x58:'iget-short',0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',
0x5c:'iput-boolean',0x5d:'iput-byte',0x5e:'iput-char',0x5f:'iput-short',
0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x63:'sget-boolean',0x64:'sget-byte',
0x65:'sget-char',0x66:'sget-short',0x67:'sput',0x68:'sput-wide',0x69:'sput-object',
0x6a:'sput-boolean',0x6b:'sput-byte',0x6c:'sput-char',0x6d:'sput-short',
0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',
0x72:'invoke-interface',0x74:'invoke-virtual/range',0x75:'invoke-super/range',
0x76:'invoke-direct/range',0x77:'invoke-static/range',0x78:'invoke-interface/range',
}
for i in range(0x79, 0xaf):
    OPCODES[i] = ['add-int','sub-int','mul-int','div-int','rem-int','and-int','or-int',
        'xor-int','shl-int','shr-int','ushr-int','add-long','sub-long','mul-long','div-long',
        'rem-long','and-long','or-long','xor-long','shl-long','shr-long','ushr-long',
        'add-float','sub-float','mul-float','div-float','rem-float','add-double','sub-double',
        'mul-double','div-double','rem-double','add-int/2addr','sub-int/2addr','mul-int/2addr',
        'div-int/2addr','rem-int/2addr','and-int/2addr','or-int/2addr','xor-int/2addr',
        'shl-int/2addr','shr-int/2addr','ushr-int/2addr','add-long/2addr','sub-long/2addr',
        'mul-long/2addr','div-long/2addr','rem-long/2addr','and-long/2addr','or-long/2addr',
        'xor-long/2addr','shl-long/2addr','shr-long/2addr','ushr-long/2addr','add-float/2addr',
        'sub-float/2addr','mul-float/2addr','div-float/2addr','rem-float/2addr','add-double/2addr',
        'sub-double/2addr','mul-double/2addr','div-double/2addr','rem-double/2addr'][i-0x79]
for i in range(0xb0, 0xc8):
    OPCODES[i] = ['add-int/2addr','sub-int/2addr','mul-int/2addr','div-int/2addr','rem-int/2addr',
        'and-int/2addr','or-int/2addr','xor-int/2addr','shl-int/2addr','shr-int/2addr','ushr-int/2addr',
        'add-long/2addr','sub-long/2addr','mul-long/2addr','div-long/2addr','rem-long/2addr',
        'and-long/2addr','or-long/2addr','xor-long/2addr','shl-long/2addr','shr-long/2addr','ushr-long/2addr',
        'add-float/2addr','sub-float/2addr','mul-float/2addr','div-float/2addr','rem-float/2addr',
        'add-double/2addr','sub-double/2addr','mul-double/2addr','div-double/2addr','rem-double/2addr'][i-0xb0]
for i in range(0xd0, 0xd8):
    OPCODES[i] = ['add-int/lit16','rsub-int','mul-int/lit16','div-int/lit16','rem-int/lit16',
        'and-int/lit16','or-int/lit16','xor-int/lit16'][i-0xd0]
for i in range(0xd8, 0xe2):
    OPCODES[i] = ['add-int/lit8','rsub-int/lit8','mul-int/lit8','div-int/lit8','rem-int/lit8',
        'and-int/lit8','or-int/lit8','xor-int/lit8','shl-int/lit8','shr-int/lit8'][i-0xd8]

class Dex:
    def __init__(self, b):
        self.b = b
        (self.string_ids_size, self.string_ids_off) = struct.unpack_from('<II', b, 0x38)
        (self.type_ids_size, self.type_ids_off) = struct.unpack_from('<II', b, 0x40)
        (self.proto_ids_size, self.proto_ids_off) = struct.unpack_from('<II', b, 0x48)
        (self.field_ids_size, self.field_ids_off) = struct.unpack_from('<II', b, 0x50)
        (self.method_ids_size, self.method_ids_off) = struct.unpack_from('<II', b, 0x58)
        (self.class_defs_size, self.class_defs_off) = struct.unpack_from('<II', b, 0x60)

    def uleb(self, p):
        shift = 0; r = 0
        while True:
            x = self.b[p]; p += 1
            r |= (x & 0x7f) << shift
            if not (x & 0x80): return r, p
            shift += 7

    def string(self, idx):
        off = struct.unpack_from('<I', self.b, self.string_ids_off + 4*idx)[0]
        r, p = self.uleb(off)
        return self.b[p:p+r].decode('utf-8', 'replace')

    def type(self, idx):
        return self.string(struct.unpack_from('<I', self.b, self.type_ids_off + 4*idx)[0])

    def field(self, idx):
        cls, typ, name = struct.unpack_from('<HHI', self.b, self.field_ids_off + 8*idx)
        return self.type(cls), self.string(name), self.type(typ)

    def method(self, idx):
        cls, proto, name = struct.unpack_from('<HHI', self.b, self.method_ids_off + 8*idx)
        return self.type(cls), self.string(name)

    def find_class_offsets(self, cls):
        """yield (cvoff, cdiroff) for class and its superclass chain roots"""
        for i in range(self.class_defs_size):
            off = self.class_defs_off + 32*i
            cls_idx = struct.unpack_from('<I', self.b, off)[0]
            if self.type(cls_idx) == cls:
                cvoff = struct.unpack_from('<I', self.b, off+24)[0]
                yield cvoff

    def disasm_method(self, cvoff, want):
        p = cvoff
        static_f, p = self.uleb(p)
        inst_f, p = self.uleb(p)
        direct_m, p = self.uleb(p)
        virtual_m, p = self.uleb(p)
        for _ in range(static_f):
            _, p = self.uleb(p); _, p = self.uleb(p)  # field_idx_diff + access_flags
        for _ in range(inst_f):
            _, p = self.uleb(p); _, p = self.uleb(p)
        found = []
        for grp in (direct_m, virtual_m):
            mi_base = 0  # empirical: each list's diffs restart (D0=70->clinit, V-accum->117=onCreate)
            for _ in range(grp):
                diff, p = self.uleb(p)
                mi_base += diff
                acc, p = self.uleb(p)
                code_off, p = self.uleb(p)
                mcls, mname = self.method(mi_base)
                if want in ('all', mname):
                    found.append((mcls, mname, code_off))
        return found

    def decode_code(self, code_off):
        b = self.b
        regs, ins = struct.unpack_from('<HH', b, code_off+4)
        outs, tries = struct.unpack_from('<HH', b, code_off+6)
        insns_size, = struct.unpack_from('<I', b, code_off+12)
        base = code_off + 16
        return regs, ins, insns_size, base

def fmt_unit(u):
    op = u & 0xff
    name = OPCODES.get(op, f'op-{op:#04x}')
    return op, name, u >> 8

def main():
    z = zipfile.ZipFile(APK)
    dexnames = [n for n in z.namelist() if n.endswith('.dex')]
    for dn in dexnames:
        dex = Dex(z.read(dn))
        for cvoff in dex.find_class_offsets(CLS):
            if not cvoff:
                continue
            found = dex.disasm_method(cvoff, METH)
            for mcls, mname, code_off in found:
                if not code_off:
                    print(f'== {mcls}.{mname} (abstract/native, no code)')
                    continue
                regs, ins, size, base = dex.decode_code(code_off)
                print(f'== {mcls}.{mname} regs={regs} ins={ins} insns={size}')
                units = struct.unpack_from(f'<{size}H', dex.b, base)
                i = 0
                while i < len(units):
                    op, name, hi = fmt_unit(units[i])
                    pc = i*2
                    line = f'{pc:#06x}: {name}'
                    # arg decoding for common formats
                    if name in ('invoke-virtual','invoke-super','invoke-direct','invoke-static','invoke-interface'):
                        mi = units[i+1]
                        mc, mn = dex.method(mi)
                        sz = (hi >> 4) & 0xf
                        line += f' {{args={sz}}} {mc}.{mn}'
                        print(line); i += 2; continue
                    if name.endswith('/range'):
                        mi = units[i+1]
                        mc, mn = dex.method(mi)
                        line += f' {mc}.{mn}'
                        print(line); i += 2; continue
                    if name in ('iget','iget-wide','iget-object','iget-boolean','iget-byte','iget-char','iget-short',
                                'iput','iput-wide','iput-object','iput-boolean','iput-byte','iput-char','iput-short'):
                        fi = units[i+1]
                        fc, fn, ft = dex.field(fi)
                        line += f' v{hi&0xf} <- {fc}.{fn}:{ft}' if name.startswith('iget') else f' v{hi&0xf} -> {fc}.{fn}:{ft}'
                        print(line); i += 2; continue
                    if name in ('sget','sget-wide','sget-object','sget-boolean','sget-byte','sget-char','sget-short',
                                'sput','sput-wide','sput-object','sput-boolean','sput-byte','sput-char','sput-short'):
                        fi = units[i+1]
                        fc, fn, ft = dex.field(fi)
                        line += f' v{hi&0xf} {"<-" if name.startswith("sget") else "->"} {fc}.{fn}:{ft}'
                        print(line); i += 2; continue
                    if name in ('const-string','const-string/jumbo'):
                        si = units[i+1]
                        line += f' v{hi&0xf} "{dex.string(si)}"'
                        print(line); i += 2; continue
                    if name in ('new-instance','const-class','check-cast'):
                        ti = units[i+1]
                        line += f' v{hi&0xf} {dex.type(ti)}'
                        print(line); i += 2; continue
                    if name == 'const/4':
                        v = hi & 0xf
                        if v >= 8: v -= 16
                        line += f' v{(hi>>4)&0xf}, {v}'
                        print(line); i += 1; continue
                    if name == 'const/16' or name == 'const-wide/16':
                        v = units[i+1]
                        if v >= 0x8000: v -= 0x10000
                        line += f' v{hi&0xff}, {v}'
                        print(line); i += 2; continue
                    if name == 'const/high16':
                        line += f' v{hi&0xff}, {units[i+1]<<16:#x}'
                        print(line); i += 2; continue
                    if name.startswith('if-') and name not in ('if-eq','if-ne','if-lt','if-ge','if-gt','if-le'):
                        tgt = pc + (hi if hi < 0x8000 else hi-0x10000)*2
                        line += f' v{hi&0xf} -> {tgt:#06x}'
                        print(line); i += 1; continue
                    if name in ('if-eq','if-ne','if-lt','if-ge','if-gt','if-le'):
                        tgt = pc + (units[i+1] if units[i+1] < 0x8000 else units[i+1]-0x10000)*2
                        line += f' v{hi&0xf}, v{(hi>>4)&0xf} -> {tgt:#06x}'
                        print(line); i += 2; continue
                    if name == 'goto':
                        off = hi if hi < 0x80 else hi-0x100
                        line += f' -> {pc+off*2:#06x}'
                        print(line); i += 1; continue
                    if name == 'goto/16':
                        off = units[i+1] if units[i+1] < 0x8000 else units[i+1]-0x10000
                        line += f' -> {pc+off*2:#06x}'
                        print(line); i += 2; continue
                    if name in ('move-result','move-result-wide','move-result-object','move-exception','return-void','return','return-wide','return-object','nop','throw','monitor-enter','monitor-exit','array-length'):
                        if hi: line += f' v{hi&0xff}'
                        print(line); i += 1; continue
                    if name in ('instance-of',):
                        ti = units[i+1]
                        line += f' v{hi&0xf}, v{(hi>>4)&0xf}, {dex.type(ti)}'
                        print(line); i += 2; continue
                    # fallback: print raw
                    line += f' [raw hi={hi:#06x} next={units[i+1]:#06x}]'
                    print(line)
                    i += 2 if op not in (0x12,) else 1

if __name__ == '__main__':
    main()
