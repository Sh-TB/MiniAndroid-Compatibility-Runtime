#!/usr/bin/env python3
"""Clean DEX method dumper for dooz APK (S33 R-NEW-332 evidence).
Usage: dump_method.py <Lclass;> <method_name> [short_descriptor]
"""
import sys, zipfile, struct, io

APK = '/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk'

class Dex:
    def __init__(self, path):
        z = zipfile.ZipFile(path)
        self.data = z.read([n for n in z.namelist() if n.endswith('.dex')][0])
        d = self.data
        self.ssz, self.sof = struct.unpack_from('<II', d, 0x38)
        self.tsz, self.tof = struct.unpack_from('<II', d, 0x40)
        self.psz, self.pof = struct.unpack_from('<II', d, 0x48)
        self.fsz, self.fof = struct.unpack_from('<II', d, 0x50)
        self.msz, self.mof = struct.unpack_from('<II', d, 0x58)
        self.cds, self.cdo = struct.unpack_from('<II', d, 0x60)

    def uleb(self, f):
        r = 0; s = 0
        while True:
            b = f.read(1)[0]; r |= (b & 0x7f) << s; s += 7
            if not b & 0x80: break
        return r

    def string(self, idx):
        off = struct.unpack_from('<I', self.data, self.sof + idx*4)[0]
        f = io.BytesIO(self.data); f.seek(off)
        n = self.uleb(f)
        return f.read(n).decode('utf-8', errors='replace').rstrip('\x00')

    def type(self, idx):
        return self.string(struct.unpack_from('<I', self.data, self.tof + idx*4)[0])

    def method_sig(self, midx):
        mc, mp, mn = struct.unpack_from('<HHI', self.data, self.mof + midx*8)
        name = self.string(mn)
        poff = self.pof + mp*12
        ret = self.type(struct.unpack_from('<I', self.data, poff+4)[0])
        po = struct.unpack_from('<I', self.data, poff+8)[0]
        params = []
        if po:
            ps = struct.unpack_from('<I', self.data, po)[0]
            for i in range(ps):
                params.append(self.type(struct.unpack_from('<H', self.data, po+4+i*2)[0]))
        return name, '(' + ''.join(params) + ')' + ret

    def find_method(self, cls, name, desc_prefix=''):
        d = self.data
        for ci in range(self.cds):
            off = self.cdo + ci*32
            cidx = struct.unpack_from('<I', d, off)[0]
            if self.type(cidx) != cls: continue
            cdo = struct.unpack_from('<I', d, off+24)[0]
            f = io.BytesIO(d); f.seek(cdo)
            sf = self.uleb(f); inf = self.uleb(f); dm = self.uleb(f); vm = self.uleb(f)
            for _ in range(sf): self.uleb(f); self.uleb(f)
            for _ in range(inf): self.uleb(f); self.uleb(f)
            out = []
            for cnt in (dm, vm):
                for _ in range(cnt):
                    midx = self.uleb(f); acc = self.uleb(f); code_off = self.uleb(f)
                    nm, sig = self.method_sig(midx)
                    if nm == name and sig.startswith(desc_prefix):
                        out.append((sig, code_off))
            return out
        return None

def disasm(d, code_off):
    data = d.data
    regs, ins, outs, tries, dbg, insns_size = struct.unpack_from('<HHHHII', data, code_off)
    print(f'registers={regs} ins={ins} outs={outs} insns={insns_size}')
    units = struct.unpack_from(f'<{insns_size}H', data, code_off+16)
    i = 0
    while i < insns_size:
        u = units[i]; op = u & 0xff
        # instruction width table (16-bit code units) — standard Dalvik formats
        W = {0x00:1,0x01:1,0x02:2,0x03:3,0x04:1,0x05:2,0x06:3,0x07:1,0x08:2,0x09:3,
             0x0a:1,0x0b:1,0x0c:1,0x0d:1,0x0e:1,0x0f:1,0x10:1,0x11:1,0x12:1,
             0x13:2,0x14:2,0x15:2,0x16:2,0x17:2,0x18:2,0x19:2,0x1a:2,0x1b:3,0x1c:2,
             0x1d:1,0x1e:1,0x1f:2,0x20:2,0x21:1,0x22:2,0x23:2,0x24:3,0x25:3,0x26:3,
             0x27:1,0x28:1,0x29:2,0x2a:3,0x2b:3,0x2c:3,
             0x2d:2,0x2e:2,0x2f:2,0x30:2,0x31:2,0x32:2,0x33:2,0x34:2,0x35:2,0x36:2,0x37:2,
             0x38:2,0x39:2,0x3a:2,0x3b:2,0x3c:2,0x3d:2,
             0x44:2,0x45:2,0x46:2,0x47:2,0x48:2,0x49:2,0x4a:2,0x4b:2,0x4c:2,0x4d:2,0x4e:2,
             0x4f:2,0x50:2,0x51:2,0x52:2,0x53:2,0x54:2,0x55:2,0x56:2,0x57:2,0x58:2,0x59:2,
             0x5a:2,0x5b:2,0x5c:2,0x5d:2,0x5e:2,0x5f:2,0x60:2,0x61:2,0x62:2,0x63:2,0x64:2,
             0x65:2,0x66:2,0x67:2,0x68:2,0x69:2,0x6a:2,0x6b:2,0x6c:2,0x6d:2,
             0x6e:3,0x6f:3,0x70:3,0x71:3,0x72:3,
             0x74:3,0x75:3,0x76:3,0x77:3,0x78:3,
             0x79:2,0x7a:2}
        size = W.get(op)
        if size is None:
            if 0x3e <= op <= 0x43 or op == 0x73 or op == 0x79 or op == 0x7a:
                size = 1
            elif 0x7b <= op <= 0x8f: size = 1
            elif 0x90 <= op <= 0xaf: size = 2
            elif 0xb0 <= op <= 0xcf: size = 1
            else: size = 2
        detail = ''
        try:
            if op in (0x6e,0x6f,0x70,0x71,0x72):
                idx = units[i+1] & 0xffff
                mc, mp, mn = struct.unpack_from('<HHI', data, d.mof + idx*8)
                detail = f' {d.type(mc)}.{d.string(mn)}'
            elif op in (0x74,0x75,0x76,0x77,0x78):
                idx = struct.unpack_from('<I', data, code_off+16+(i+1)*2)[0]
                mc, mp, mn = struct.unpack_from('<HHI', data, d.mof + idx*8)
                detail = f' {d.type(mc)}.{d.string(mn)}'
            elif 0x52 <= op <= 0x6d:
                fid = units[i+1]
                fc, ft, fn = struct.unpack_from('<HHI', data, d.fof + fid*8)
                detail = f' {d.type(fc)}.{d.string(fn)}'
            elif op in (0x1c,0x1f,0x22,0x23,0x24):
                detail = f' {d.type(units[i+1])}'
            elif op == 0x1a:
                detail = f' "{d.string(units[i+1])}"'
        except Exception as e:
            detail = f' <{e}>'
        NOP = {0x00:'nop',0x0e:'return-void',0x0f:'return',0x10:'return-wide',
               0x11:'return-object',0x12:'const/4',0x1d:'monitor-enter',0x1e:'monitor-exit',
               0x27:'throw',0x28:'goto',0x21:'array-length',0x0d:'move-exception'}
        if 0x01 <= op <= 0x0c: name = {1:'move',2:'move/from16',3:'move/16',4:'move-wide',5:'move-wide/from16',6:'move-wide/16',7:'move-object',8:'move-object/from16',9:'move-object/16',10:'move-result',11:'move-result-wide',12:'move-result-object'}.get(op, f'op{op:02x}')
        elif 0x13 <= op <= 0x1c: name = {0x13:'const/16',0x14:'const',0x15:'const/high16',0x16:'const-wide/16',0x17:'const-wide/32',0x18:'const-wide',0x19:'const-wide/high16',0x1a:'const-string',0x1b:'const-string/jumbo',0x1c:'const-class'}.get(op)
        elif 0x1f <= op <= 0x26: name = {0x1f:'check-cast',0x20:'instance-of',0x22:'new-instance',0x23:'new-array',0x24:'filled-new-array',0x25:'filled-new-array/range',0x26:'fill-lined'}.get(op)
        elif 0x2b <= op <= 0x2c: name = {0x2b:'packed-switch',0x2c:'sparse-switch'}.get(op)
        elif 0x2d <= op <= 0x3d: name = {0x2d:'cmpl-float',0x31:'cmp',0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',0x37:'if-le',0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez'}.get(op, f'cmp{op:02x}')
        elif 0x52 <= op <= 0x5f: name = {0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',0x56:'iget-byte',0x57:'iget-char',0x58:'iget-short',0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',0x5c:'iput-boolean',0x5d:'iput-byte',0x5e:'iput-char',0x5f:'iput-short'}.get(op)
        elif 0x60 <= op <= 0x6d: name = {0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x63:'sget-boolean',0x64:'sget-byte',0x65:'sget-char',0x66:'sget-short',0x67:'sput',0x68:'sput-wide',0x69:'sput-object',0x6a:'sput-boolean',0x6b:'sput-byte',0x6c:'sput-char',0x6d:'sput-short'}.get(op)
        elif 0x6e <= op <= 0x72: name = {0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface'}.get(op)
        elif 0x74 <= op <= 0x78: name = {0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',0x77:'invoke-static/range',0x78:'invoke-interface/range'}.get(op)
        elif 0x7b <= op <= 0x8f: name = {0x7b:'int-to-long',0x7c:'int-to-float',0x7d:'int-to-double',0x7e:'long-to-int',0x7f:'long-to-float',0x80:'long-to-double',0x81:'float-to-int',0x82:'float-to-long',0x83:'float-to-double',0x84:'double-to-int',0x85:'double-to-long',0x86:'double-to-float',0x87:'int-to-byte',0x88:'int-to-char',0x89:'int-to-short',0x8a:'add-int/2addr',0x8b:'sub-int/2addr',0x8c:'mul-int/2addr',0x8d:'div-int/2addr',0x8e:'rem-int/2addr',0x8f:'and-int/2addr'}.get(op, f'arith{op:02x}')
        elif 0x90 <= op <= 0xaf: name = {0x90:'add-int',0x91:'sub-int',0x92:'mul-int',0x93:'div-int',0x94:'rem-int',0x95:'and-int',0x96:'or-int',0x97:'xor-int',0x98:'shl-int',0x99:'shr-int',0x9a:'ushr-int',0x9b:'add-long',0x9c:'sub-long',0x9d:'mul-long',0x9e:'div-long',0x9f:'rem-long',0xa0:'and-long',0xa1:'or-long',0xa2:'xor-long',0xa3:'shl-long',0xa4:'shr-long',0xa5:'ushr-long',0xa6:'add-float',0xa7:'sub-float',0xa8:'mul-float',0xa9:'div-float',0xaa:'rem-float',0xab:'add-double',0xac:'sub-double',0xad:'mul-double',0xae:'div-double',0xaf:'rem-double'}.get(op)
        elif 0xb0 <= op <= 0xcf: name = {0xb0:'add-int/2addr',0xb1:'sub-int/2addr',0xb2:'mul-int/2addr',0xb3:'div-int/2addr',0xb4:'rem-int/2addr',0xb5:'and-int/2addr',0xb6:'or-int/2addr',0xb7:'xor-int/2addr',0xb8:'shl-int/2addr',0xb9:'shr-int/2addr',0xba:'ushr-int/2addr',0xbb:'add-long/2addr',0xbc:'sub-long/2addr',0xbd:'mul-long/2addr',0xbe:'div-long/2addr',0xbf:'rem-long/2addr',0xc0:'and-long/2addr',0xc1:'or-long/2addr',0xc2:'xor-long/2addr',0xc3:'shl-long/2addr',0xc4:'shr-long/2addr',0xc5:'ushr-long/2addr',0xc6:'add-float/2addr',0xc7:'sub-float/2addr',0xc8:'mul-float/2addr',0xc9:'div-float/2addr',0xca:'rem-float/2addr',0xcb:'add-double/2addr',0xcc:'sub-double/2addr',0xcd:'mul-double/2addr',0xce:'div-double/2addr',0xcf:'rem-double/2addr'}.get(op)
        else: name = NOP.get(op, f'op_{op:02x}')
        print(f'  {i:04d}: {name}{detail}')
        i += size

if __name__ == '__main__':
    cls, meth = sys.argv[1], sys.argv[2]
    pref = sys.argv[3] if len(sys.argv) > 3 else ''
    d = Dex(APK)
    hits = d.find_method(cls, meth, pref)
    if hits is None:
        print(f'class {cls} NOT FOUND'); sys.exit(1)
    if not hits:
        print(f'{cls}: method {meth}{pref} not found in class_data'); sys.exit(1)
    for sig, co in hits:
        print(f'=== {cls}.{meth}{sig} code_off=0x{co:x}')
        if co: disasm(d, co)
