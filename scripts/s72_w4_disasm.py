#!/usr/bin/env python3
"""s72_w4_disasm.py <apk> <Lclass;> <method> — dump method bytecode (D8 output)."""
import sys, zipfile, struct, io

def uleb(f):
    r = 0; s = 0
    while True:
        b = f.read(1)[0]; r |= (b & 0x7f) << s; s += 7
        if not b & 0x80: break
    return r

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

    def string(self, idx):
        off = struct.unpack_from('<I', self.data, self.sof + idx*4)[0]
        f = io.BytesIO(self.data); f.seek(off)
        n = uleb(f)
        return f.read(n).decode('utf-8', 'replace')

    def type_desc(self, idx):
        return self.string(struct.unpack_from('<I', self.data, self.tof + idx*4)[0])

    def find_method(self, cls, name):
        # scan class_def table
        cdsz, cdof = struct.unpack_from('<II', self.data, 0x60)
        for i in range(cdsz):
            base = cdof + i*32
            cls_idx = struct.unpack_from('<I', self.data, base)[0]
            if self.type_desc(cls_idx) != cls: continue
            co = struct.unpack_from('<I', self.data, base+6*4)[0]
            if co == 0: continue
            f = io.BytesIO(self.data); f.seek(co)
            static_size = uleb(f); inst_size = uleb(f); dm_size = uleb(f)
            for _ in range(dm_size):
                midx = uleb(f); acc = uleb(f); code_off = uleb(f)
                cls_i, proto_i, name_i = struct.unpack_from('<HHI', self.data, self.mof + midx*8)
                mname = self.string(name_i)
                if mname == name:
                    return code_off
        return None

NAMES = {0x00:'nop',0x01:'move',0x02:'move/from16',0x04:'move-wide',0x07:'move-object',0x08:'move-object/from16',
0x0b:'return-void',0x0c:'return',0x0d:'return-wide',0x0e:'return-object',0x0f:'const/4',0x10:'const/16',0x13:'const',
0x14:'const-wide/32',0x15:'const-wide',0x16:'const-wide/16',0x17:'const/high16',0x1a:'const-string',0x1c:'const-class',
0x1f:'check-cast',0x21:'instance-of',0x22:'new-instance',0x23:'new-array',0x25:'filled-new-array',0x26:'fill-array-data',
0x27:'throw',0x28:'goto',0x29:'goto/16',0x2b:'packed-switch',0x2c:'sparse-switch',0x2e:'cmpl-float',0x31:'cmpg-float',
0x33:'if-eq',0x34:'if-ne',0x35:'if-lt',0x36:'if-ge',0x37:'if-gt',0x38:'if-le',0x39:'if-eqz',0x3a:'if-nez',
0x3b:'if-ltz',0x3c:'if-gez',0x3d:'if-gtz',0x3e:'if-lez',0x44:'aget',0x46:'aget-object',0x4b:'aput',0x4f:'iget',
0x52:'iget-object',0x54:'iget-boolean',0x55:'iget-wide',0x59:'iput',0x5b:'iput-object',0x5e:'iput-wide',0x5f:'sget',
0x62:'sget-object',0x63:'sget-boolean',0x64:'sget-wide',0x67:'sput',0x69:'sput-object',0x6b:'sput-wide',0x6e:'invoke-virtual',
0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface',0x74:'invoke-virtual/range',
0x76:'invoke-direct/range',0x77:'invoke-static/range',0x78:'invoke-interface/range',0x7b:'int-to-long',0x7f:'int-to-float',
0x81:'long-to-float',0x84:'int-to-float',0x85:'int-to-double',0x8f:'long-to-float',0x90:'float-to-int',0x91:'float-to-long',
0xa0:'add-int',0xa3:'sub-int',0xab:'add-int/2addr',0xad:'sub-int/2addr',0xaf:'mul-int/2addr',0xb0:'div-int/2addr',
0xbb:'add-float/2addr',0xbd:'sub-float/2addr',0xbf:'mul-float/2addr',0xc0:'div-float/2addr',0xca:'add-long/2addr',
0xd8:'add-int/lit8',0xda:'sub-int/lit8',0xdb:'mul-int/lit8',0xdc:'div-int/lit8',0xdd:'rem-int/lit8',0xdf:'shl-int/lit8'}

def main():
    apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
    d = Dex(apk)
    off = d.find_method(cls, meth)
    if not off:
        print("method not found"); return
    dd = d.data
    insns_size, insns_of = struct.unpack_from('<II', dd, off+12)
    code = dd[insns_of:insns_of+insns_size*2]
    units = struct.unpack_from('<%dH' % insns_size, code, 0)
    pc = 0
    while pc < insns_size:
        op = units[pc] & 0xff
        name = NAMES.get(op, 'op-%02x' % op)
        line = f"{pc:4d}: {name}"
        # light operand decode for invokes (35c: BGA|meth@CCCC in next unit)
        if op in (0x6e,0x6f,0x70,0x71,0x72) and pc+2 < insns_size:
            midx = units[pc+1]
            cls_i, proto_i, name_i = struct.unpack_from('<HHI', dd, d.mof + midx*8)
            # proto: return type + params
            po = struct.unpack_from('<I', dd, d.tof + proto_i*4)[0]
            line += f" {d.type_desc(cls_i)}->{d.string(name_i)}{d.type_desc(po)}"
            pc += 3; print(line); continue
        if op == 0x0f:  # const/4
            line += f" v{units[pc]&0xf}, {((units[pc]>>8)&0xf)}"
            pc += 1; print(line); continue
        if op == 0x1a and pc+1 < insns_size:
            line += f" \"{d.string(units[pc+1])[:40]}\""
            pc += 2; print(line); continue
        if op in (0x39,0x3a,0x3b,0x3c,0x3d,0x3e):
            line += f" v{units[pc]&0xf}, +{struct.unpack_from('<h', code, (pc+1)*2)[0]*2+pc*2}"
            pc += 2; print(line); continue
        if op in (0x33,0x34,0x35,0x36,0x37,0x38):
            tgt = struct.unpack_from('<h', code, (pc+2)*2)[0]
            line += f" v{units[pc]&0xf}, v{(units[pc]>>8)&0xf}, +{tgt*2+pc*2}"
            pc += 3; print(line); continue
        if op == 0x28:
            line += f" +{struct.unpack_from('<b', code, pc*2+1)[0]*2+pc*2}"
            pc += 1; print(line); continue
        if op == 0x28 or op == 0x29:
            pass
        if op in (0x10,0x13,0x62,0x5f,0x52,0x59,0x5b,0x69,0x6b,0x21,0x22,0x1c,0x1f,0x23,0x6a,0x54,0x55,0x5e,0x63,0x64,0x67,0xd8,0xda,0xdb,0xdc,0xdd,0xdf) and pc+1 < insns_size:
            operands = units[pc+1]
            line += f" ({operands:04x})"
            if op in (0x62,0x5f,0x52,0x5b,0x69,0x22,0x1c,0x1f,0x23):
                # field/type index
                try:
                    if op in (0x22,0x1c,0x1f,0x23): line += f" type={d.type_desc(operands)}"
                except Exception: pass
            pc += 2; print(line); continue
        pc += 1
        print(line)

main()
