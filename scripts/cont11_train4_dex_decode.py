#!/usr/bin/env python3
"""TRAIN-4 car-2: DEFINITIVE decode of Ld61; (Placeable.MeasurePassDelegate, compose 1.6.7 R8) from dooz APK.
Goals:
  1. Full field list (name+type+order) + full method table (name+REAL descriptor) of Ld61;
  2. Full disassembly of i0 / m0 / l0 / <init> -> identify i0 semantically against the
     now-in-hand 1.6.7 sources (Placeable.kt + LayoutNodeLayoutDelegate.kt).
  3. Lqi0; method .i descriptor + shape (caller of i0 x6358).
Authoritative opcode widths from scripts/dalvik_walker.py (calibrated).
"""
import sys, zipfile, struct, io

APK = '/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apk'

def uleb(buf, off):
    r, s = 0, 0
    while True:
        b = buf[off]; off += 1
        r |= (b & 0x7F) << s
        if not (b & 0x80): break
        s += 7
    return r, off

class Dex:
    def __init__(self, b):
        self.b = b
        (self.ssz, self.sof) = struct.unpack_from('<II', b, 0x38)
        (self.tsz, self.tof) = struct.unpack_from('<II', b, 0x40)
        (self.psz, self.pof) = struct.unpack_from('<II', b, 0x48)
        (self.fsz, self.fof) = struct.unpack_from('<II', b, 0x50)
        (self.msz, self.mof) = struct.unpack_from('<II', b, 0x58)
        (self.cds, self.cdo) = struct.unpack_from('<II', b, 0x60)
        self._sc = {}
    def str_at(self, i):
        if i in self._sc: return self._sc[i]
        off = struct.unpack_from('<I', self.b, self.sof + i*4)[0]
        n, o = uleb(self.b, off)
        end = o
        while self.b[end] != 0: end += 1
        s = self.b[o:end].decode('utf-8', 'replace')
        self._sc[i] = s
        return s
    def type_at(self, i): return self.str_at(struct.unpack_from('<I', self.b, self.tof + i*4)[0])
    def field_at(self, i):
        c, t, n = struct.unpack_from('<HHI', self.b, self.fof + i*8)
        return self.type_at(c), self.str_at(n), self.type_at(t)
    def method_at(self, i):
        c, p, n = struct.unpack_from('<HHI', self.b, self.mof + i*8)
        return self.type_at(c), self.str_at(n), self.proto(p)
    def proto(self, p):
        _shorty, ri = struct.unpack_from('<II', self.b, self.pof + p*12)
        o = struct.unpack_from('<I', self.b, self.pof + p*12 + 8)[0]
        params = []
        if o:
            cnt = struct.unpack_from('<I', self.b, o)[0]
            for k in range(cnt):
                params.append(self.type_at(struct.unpack_from('<H', self.b, o+4+k*2)[0]))
        return '(' + ''.join(params) + ')' + self.type_at(ri)
    def find_class(self, desc):
        for i in range(self.cds):
            off = self.cdo + i*32
            ci, = struct.unpack_from('<I', self.b, off)
            if self.type_at(ci) == desc: return off
        return None
    def class_data(self, off):
        b = self.b
        cdo, = struct.unpack_from('<I', b, off + 24)
        sup, = struct.unpack_from('<I', b, off + 8)
        if cdo == 0: return self.type_at(sup), [], []
        p = cdo
        sf, p = uleb(b, p); inf, p = uleb(b, p)
        dm, p = uleb(b, p); vm, p = uleb(b, p)
        fields = []
        for lst_start, lst_count in ((0, sf), (1, inf)):
            fidx = 0  # reset per list (first element of each list is absolute)
            for _ in range(lst_count):
                d, p = uleb(b, p); fidx += d
                acc, p = uleb(b, p)
                cn, fn, ft = self.field_at(fidx)
                fields.append((fn, ft, acc))
        methods = []
        # DEX SPEC: "The index of the first element in a list is represented
        # directly" — the idx accumulator RESETS at the start of EACH list
        # (static_fields / instance_fields / direct_methods / virtual_methods).
        # Carrying midx across direct->virtual desyncs every such class.
        for kind, count in (('direct', dm), ('virtual', vm)):
            midx = 0
            for _ in range(count):
                d, p = uleb(b, p); midx += d
                acc, p = uleb(b, p)
                code_off, p = uleb(b, p)
                cn, mn, desc = self.method_at(midx)
                methods.append((kind, cn, mn, desc, code_off))
        return self.type_at(sup), fields, methods
    def code(self, code_off):
        b = self.b
        if code_off == 0: return 0, 0, [], []
        regs, ins = struct.unpack_from('<HH', b, code_off)
        ssz, = struct.unpack_from('<I', b, code_off + 12)
        units = list(struct.unpack_from('<%dH' % ssz, b, code_off + 16))
        # try/catch + debug skipped (not needed)
        return regs, ins, units, []

W = [1]*256
def _setw(a, e, w):
    for o in range(a, e+1): W[o] = w
W[0x00]=1; W[0x01]=1; W[0x02]=1; W[0x03]=1; W[0x04]=1; W[0x05]=1; W[0x06]=1; W[0x07]=1
W[0x08]=1; W[0x09]=1; W[0x0a]=1; W[0x0b]=1; W[0x0c]=1; W[0x0d]=1; W[0x0e]=1; W[0x0f]=1
W[0x10]=1; W[0x11]=1
W[0x12]=1; W[0x13]=2; W[0x14]=3; W[0x15]=2; W[0x16]=2; W[0x17]=3; W[0x18]=5; W[0x19]=2
W[0x1a]=2; W[0x1b]=3; W[0x1c]=2; W[0x1d]=1; W[0x1e]=1; W[0x1f]=2; W[0x20]=2; W[0x21]=1
W[0x22]=2; W[0x23]=2; W[0x24]=3; W[0x25]=3; W[0x26]=3; W[0x27]=1; W[0x28]=1; W[0x29]=2
W[0x2a]=3; W[0x2b]=3; W[0x2c]=3
_setw(0x2d, 0x31, 2); _setw(0x32, 0x37, 2); _setw(0x38, 0x3d, 2)
_setw(0x44, 0x51, 2); _setw(0x52, 0x6d, 2)
_setw(0x6e, 0x72, 3); _setw(0x74, 0x78, 3)
_setw(0x7b, 0x8f, 1); _setw(0x90, 0xaf, 2); _setw(0xb0, 0xcf, 1)
_setw(0xd0, 0xd7, 2); _setw(0xd8, 0xe2, 2)
W[0xfa]=4; W[0xfb]=4; W[0xfc]=3; W[0xfd]=3; W[0xfe]=2; W[0xff]=2

BINOPS = {0x90:'add-int',0x91:'sub-int',0x92:'mul-int',0x93:'div-int',0x94:'rem-int',0x95:'and-int',0x96:'or-int',0x97:'xor-int',0x98:'shl-int',0x99:'shr-int',0x9a:'ushr-int',0x9b:'add-long',0x9c:'sub-long',0x9d:'mul-long',0x9e:'div-long',0x9f:'rem-long',0xa0:'and-long',0xa1:'or-long',0xa2:'xor-long',0xa3:'shl-long',0xa4:'shr-long',0xa5:'ushr-long',0xa6:'add-float',0xa7:'sub-float',0xa8:'mul-float',0xa9:'div-float',0xaa:'rem-float',0xab:'add-double',0xac:'sub-double',0xad:'mul-double',0xae:'div-double',0xaf:'rem-double'}
BIN2 = {0xb0:'add-int/2addr',0xb1:'sub-int/2addr',0xb2:'mul-int/2addr',0xb3:'div-int/2addr',0xb4:'rem-int/2addr',0xb5:'and-int/2addr',0xb6:'or-int/2addr',0xb7:'xor-int/2addr',0xb8:'shl-int/2addr',0xb9:'shr-int/2addr',0xba:'ushr-int/2addr',0xbb:'add-long/2addr',0xbc:'sub-long/2addr',0xbd:'mul-long/2addr',0xbe:'div-long/2addr',0xbf:'rem-long/2addr',0xc0:'and-long/2addr',0xc1:'or-long/2addr',0xc2:'xor-long/2addr',0xc3:'shl-long/2addr',0xc4:'shr-long/2addr',0xc5:'ushr-long/2addr',0xc6:'add-float/2addr',0xc7:'sub-float/2addr',0xc8:'mul-float/2addr',0xc9:'div-float/2addr',0xca:'rem-float/2addr',0xcb:'add-double/2addr',0xcc:'sub-double/2addr',0xcd:'mul-double/2addr',0xce:'div-double/2addr',0xcf:'rem-double/2addr'}
UNI = {0x7b:'int-to-long',0x7c:'int-to-float',0x7d:'int-to-double',0x7e:'long-to-int',0x7f:'long-to-float',0x80:'long-to-double',0x81:'float-to-int',0x82:'float-to-long',0x83:'float-to-double',0x84:'double-to-int',0x85:'double-to-long',0x86:'double-to-float',0x87:'int-to-byte',0x88:'int-to-char',0x89:'int-to-short',0x8a:'neg-int',0x8b:'not-int',0x8c:'neg-long',0x8d:'not-long',0x8e:'neg-float',0x8f:'neg-double'}
CMP = {0x2d:'cmpl-float',0x2e:'cmpg-float',0x2f:'cmpl-double',0x30:'cmpg-double',0x31:'cmp-long'}
IGET = {0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',0x56:'iget-byte',0x57:'iget-char',0x58:'iget-short',0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',0x5c:'iput-boolean',0x5d:'iput-byte',0x5e:'iput-char',0x5f:'iput-short',0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x63:'sget-boolean',0x64:'sget-byte',0x65:'sget-char',0x66:'sget-short',0x67:'sput',0x68:'sput-wide',0x69:'sput-object',0x6a:'sput-boolean',0x6b:'sput-byte',0x6c:'sput-char',0x6d:'sput-short'}
INV = {0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface',0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',0x77:'invoke-static/range',0x78:'invoke-interface/range'}
IF = {0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',0x37:'if-le',0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez'}

def s4(v):
    return v if v < 0x10 else v - 0x10

def disasm(d, units):
    out = []
    i, n = 0, len(units)
    while i < n:
        u = units[i]; op = u & 0xff; w = W[op]
        if w == 0: w = 1
        pc = i
        if op == 0x00:
            hi = u >> 8
            if hi == 0x01:
                sz = units[i+1]; i += 4 + sz; continue
            if hi == 0x02:
                sz = units[i+1]; i += 2 + 4*sz; continue
            if hi == 0x03:
                sz = units[i+1]; i += 4 + 2*sz; continue
            out.append((pc, 'nop', '')); i += 1; continue
        if op in IGET:
            cls, fn, ft = d.field_at(units[i+1])
            out.append((pc, IGET[op], f'v{u>>8}, {cls}.{fn}:{ft}')); i += w; continue
        if op in INV:
            if op in (0xfb, 0xfd):
                midx = units[i+2]
            else:
                midx = units[i+1]
            cls, mn, desc = d.method_at(midx)
            areg = ''
            if op < 0x74:
                cnt = (u >> 12) & 0xf
                regs = [str(s4(units[i+1] >> (4*k) & 0xf)) for k in range(4)]
                regs = regs[:cnt]
                if cnt == 5: regs = [str(units[i+2] >> 8)] + regs
                areg = ' {' + ', '.join(regs) + '}'
            out.append((pc, INV[op], f'{cls}->{mn}{desc}{areg}')); i += w; continue
        if op in IF:
            if op < 0x38:
                out.append((pc, IF[op], f'v{s4(units[i+1]&0xf)}, v{units[i+1]>>4}, +{units[i+2]}')); i += w; continue
            out.append((pc, IF[op], f'v{u>>8}, +{units[i+1]}')); i += w; continue
        if op in BINOPS:
            out.append((pc, BINOPS[op], f'v{u>>8}, v{units[i+1]&0xff}, v{units[i+1]>>8}')); i += w; continue
        if op in BIN2:
            out.append((pc, BIN2[op], f'v{u>>8&0xf}, v{u>>12}')); i += w; continue
        if op in UNI:
            out.append((pc, UNI[op], f'v{u>>8}, v{units[i+1]&0xff}')); i += w; continue
        if op in CMP:
            out.append((pc, CMP[op], f'v{u>>8}, v{units[i+1]&0xff}, v{units[i+1]>>8}')); i += w; continue
        if op == 0x12:  # const/4
            out.append((pc, 'const/4', f'v{u>>8}, #{s4((u>>12)&0xf)}')); i += w; continue
        if op == 0x13:
            out.append((pc, 'const/16', f'v{u>>8}, #{struct.unpack_from("<h", struct.pack("<H", units[i+1]))[0]}')); i += w; continue
        if op == 0x14:
            v = units[i+1] | (units[i+2] << 16)
            out.append((pc, 'const', f'v{u>>8}, #{v if v < 0x80000000 else v-(1<<32)}')); i += w; continue
        if op == 0x16:
            v = units[i+1]
            out.append((pc, 'const-wide/16', f'v{u>>8}, #{v if v < 0x8000 else v-(1<<16)}')); i += w; continue
        if op == 0x18:
            v = units[i+1] | (units[i+2]<<16) | (units[i+3]<<32) | (units[i+4]<<48)
            out.append((pc, 'const-wide', f'v{u>>8}, #{v}')); i += w; continue
        if op == 0x1a:
            out.append((pc, 'const-string', f'v{u>>8}, "{d.str_at(units[i+1])[:60]}"')); i += w; continue
        if op == 0x22:
            out.append((pc, 'new-instance', f'v{u>>8}, {d.type_at(units[i+1])}')); i += w; continue
        if op == 0x1f:
            out.append((pc, 'check-cast', f'v{u>>8}, {d.type_at(units[i+1])}')); i += w; continue
        if op == 0x20:
            out.append((pc, 'instance-of', f'v{u>>8&0xf}, {d.type_at(units[i+1])}')); i += w; continue
        if 0x01 <= op <= 0x0c:
            names = {1:'move',2:'move/from16',4:'move-wide',5:'move-wide/from16',7:'move-object',8:'move-object/from16'}
            if op in names:
                if op in (2,5,8): out.append((pc, names[op], f'v{u>>8}, v{units[i+1]}')); i += w; continue
                out.append((pc, names[op], f'v{u>>8&0xf}, v{u>>12}')); i += w; continue
            out.append((pc, f'move-op{op:02x}', f'v{u>>8&0xf}, v{u>>12}')); i += w; continue
        if op in (0x0d, 0x11, 0x1d, 0x1e, 0x21, 0x27, 0x28):
            names = {0x0d:'move-exception',0x11:'move-result-object',0x1d:'monitor-enter',0x1e:'monitor-exit',0x21:'array-length',0x27:'throw',0x28:'goto'}
            out.append((pc, names[op], f'v{u>>8}')); i += w; continue
        if op in (0x0e, 0x0f, 0x10):
            names = {0x0e:'return-void',0x0f:'return',0x10:'return-wide'}
            out.append((pc, names[op], '')); i += w; continue
        if op == 0x0a:
            out.append((pc, 'move-result', f'v{u>>8}')); i += w; continue
        if op == 0x0b:
            out.append((pc, 'move-result-wide', f'v{u>>8}')); i += w; continue
        if op == 0x23:
            out.append((pc, 'new-array', f'v{u>>8&0xf}, v{u>>12}, {d.type_at(units[i+1])}')); i += w; continue
        if 0x44 <= op <= 0x51:
            fam = {0x44:'aget',0x45:'aget-wide',0x46:'aget-object',0x4b:'aput',0x4c:'aput-wide',0x4d:'aput-object'}
            out.append((pc, fam.get(op, f'arr-op{op:02x}'), f'v{u>>8&0xf}, v{u>>12}, v{units[i+1]&0xff}')); i += w; continue
        if 0xd8 <= op <= 0xe2:
            fam = {0xd8:'add-int/lit8',0xd9:'sub-int/lit8',0xda:'mul-int/lit8',0xdb:'div-int/lit8',0xdc:'rem-int/lit8',0xdd:'and-int/lit8',0xde:'or-int/lit8',0xdf:'xor-int/lit8',0xe0:'shl-int/lit8',0xe1:'shr-int/lit8',0xe2:'ushr-int/lit8'}
            lit = units[i+2] & 0xff
            if lit >= 0x80: lit -= 256
            out.append((pc, fam[op], f'v{u>>8}, v{units[i+1]&0xff}, #{lit}')); i += w; continue
        if 0xd0 <= op <= 0xd7:
            fam = {0xd0:'add-int/lit16',0xd1:'sub-int/lit16',0xd2:'mul-int/lit16'}
            lit = units[i+1] & 0xffff
            if lit >= 0x8000: lit -= 65536
            out.append((pc, fam.get(op, f'lit16-op{op:02x}'), f'v{u>>8}, v{units[i+1]>>8&0xff} wait, #{lit}')); i += w; continue
        out.append((pc, f'op{op:02x}', f'{u:04x}')); i += w; continue
    return out

def main():
    z = zipfile.ZipFile(APK)
    targets = ['Ld61;', 'Lqi0;']
    for dn in sorted(n for n in z.namelist() if n.endswith('.dex')):
        b = z.read(dn)
        d = Dex(b)
        for t in targets:
            off = d.find_class(t)
            if off is None: continue
            sup, fields, methods = d.class_data(off)
            print(f'== {dn} {t} super={sup}')
            if t == 'Ld61;':
                print('  FIELDS:')
                for fn, ft, acc in fields:
                    print(f'    {fn} : {ft}  acc=0x{acc:x}')
            print('  METHODS:')
            for kind, cn, mn, desc, code_off in methods:
                print(f'    {kind} {mn}{desc} code_off={code_off}')
            want = set()
            if t == 'Ld61;':
                want = {'i0', 'm0', 'l0'}
            else:
                want = {'i'}
            for kind, cn, mn, desc, code_off in methods:
                if mn not in want: continue
                regs, ins, units, _ = d.code(code_off)
                print(f'  --- DISASM {cn}.{mn}{desc} regs={regs} ins={ins} units={len(units)}')
                for pc, tag, val in disasm(d, units):
                    print(f'    +{pc:05d} {tag} {val}')

if __name__ == '__main__':
    main()
