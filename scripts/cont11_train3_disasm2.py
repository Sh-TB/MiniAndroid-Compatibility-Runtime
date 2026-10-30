#!/usr/bin/env python3
"""CONT-11 TRAIN-3: precise disassembler for dooz v23 classes.dex.
Usage: cont11_train3_disasm2.py <Lcls;> <method> [proto-substr]
Finds ALL method_ids entries matching class+name (handles overloads),
locates the code_item via class_data (direct+virtual, uleb diff laws),
prints a readable instruction listing.
"""
import sys, zipfile, struct, io

APK = '/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apk'

def uleb(f):
    r = 0; sh = 0
    while True:
        b = f.read(1)[0]; r |= (b & 0x7f) << sh; sh += 7
        if not (b & 0x80): break
    return r

class Dex:
    def __init__(self, data):
        self.d = data
        (self.str_n, self.str_o) = struct.unpack_from('<II', data, 0x38)
        (self.type_n, self.type_o) = struct.unpack_from('<II', data, 0x40)
        (self.proto_n, self.proto_o) = struct.unpack_from('<II', data, 0x48)
        (self.fid_n, self.fid_o) = struct.unpack_from('<II', data, 0x50)
        (self.mid_n, self.mid_o) = struct.unpack_from('<II', data, 0x58)
        (self.cls_n, self.cls_o) = struct.unpack_from('<II', data, 0x60)

    def s(self, i):
        off = struct.unpack_from('<I', self.d, self.str_o + i*4)[0]
        f = io.BytesIO(self.d); f.seek(off)
        n = uleb(f); return f.read(n).decode('utf-8', 'replace')

    def t(self, i):
        return self.s(struct.unpack_from('<I', self.d, self.type_o + i*4)[0])

    def fid(self, i):
        cls_t, type_t, name_i = struct.unpack_from('<HHI', self.d, self.fid_o + i*8)
        return self.t(cls_t), self.s(name_i), self.t(type_t)

    def mid(self, i):
        cls_t, proto_t, name_i = struct.unpack_from('<HHI', self.d, self.mid_o + i*8)
        return self.t(cls_t), self.s(name_i), self.proto_str(proto_t)

    def proto_str(self, idx):
        base = self.proto_o + idx * 12
        ret_t = struct.unpack_from('<H', self.d, base + 4)[0]
        po = struct.unpack_from('<I', self.d, base + 8)[0]
        params = []
        if po:
            n = struct.unpack_from('<I', self.d, po)[0]
            params = [self.t(struct.unpack_from('<H', self.d, po + 4 + k*2)[0]) for k in range(n)]
        return f"({','.join(params)}){self.t(ret_t)}"

    def methods_of(self, cls):
        """Return list of (name, proto, code_off, midx_abs) for all members."""
        for ci in range(self.cls_n):
            off = self.cls_o + ci*32
            (cidx, acc, sup, ifs, src, an, cdo, sv) = struct.unpack_from('<8I', self.d, off)
            if self.t(cidx) != cls:
                continue
            if cdo == 0:
                return []
            f = io.BytesIO(self.d); f.seek(cdo)
            sf = uleb(f); inf = uleb(f); dm = uleb(f); vm = uleb(f)
            for _ in range(sf + inf):
                uleb(f); uleb(f)
            out = []
            for section in ('direct', 'virtual'):
                midx = 0
                for k in range(dm if section == 'direct' else vm):
                    d = uleb(f); acc2 = uleb(f); code_off = uleb(f)
                    midx = d if k == 0 else midx + d
                    c, n, p = self.mid(midx)
                    out.append((n, p, code_off, midx))
            return out
        return []

    def read_code(self, code_off):
        regs = struct.unpack_from('<H', self.d, code_off + 0)[0]
        ins = struct.unpack_from('<H', self.d, code_off + 2)[0]
        outs = struct.unpack_from('<H', self.d, code_off + 4)[0]
        insns_sz = struct.unpack_from('<I', self.d, code_off + 12)[0]
        insns_off = code_off + 16
        return regs, self.d[insns_off:insns_off + insns_sz*2]

# opcode table: op -> (name, code-unit size, format)
def fmt1(n, k='x'): return (n, 1, k)
OPS = {}
for op, nm in [(0x00,'nop'),(0x0e,'return-void'),(0x1d,'monitor-enter'),(0x1e,'monitor-exit'),
               (0x26,'throw'),(0x27,'goto/16')]:
    OPS[op] = (nm, 1, 'none')
OPS[0x28] = ('goto', 1, 'none')
for op, nm in [(0x01,'move'),(0x04,'move-wide'),(0x07,'move-object'),(0x0a,'move-result'),
               (0x0b,'move-result-wide'),(0x0c,'move-result-object'),(0x0d,'move-exception'),
               (0x0f,'return'),(0x10,'return-wide'),(0x11,'return-object'),
               (0x62,'sget'),(0x63,'sget-wide'),
               (0x64,'sget-object'),(0x65,'sget-boolean'),(0x66,'sget-byte'),(0x67,'sget-char'),
               (0x68,'sget-short'),(0x69,'sput'),(0x6a,'sput-wide'),(0x6b,'sput-object'),
               (0x6c,'sput-boolean'),(0x6d,'sput-byte')]:
    OPS[op] = (nm, 1, 'reg')
for op, nm in [(0x6e,'invoke-virtual'),(0x6f,'invoke-super'),(0x70,'invoke-direct'),
               (0x71,'invoke-static'),(0x72,'invoke-interface')]:
    OPS[op] = (nm, 3, 'invoke35c')
for op, nm in [(0x1c,'const-class'),(0x1f,'check-cast'),(0x22,'new-instance')]:
    OPS[op] = (nm, 2, 'type2')
for op, nm in [(0x12,'const/4')]:
    OPS[op] = (nm, 1, 'lit4')
for op, nm in [(0x13,'const/16'),(0x16,'const-wide/16')]:
    OPS[op] = (nm, 2, 'lit16reg')
OPS[0x1a] = ('const-string', 2, 'str')
OPS[0x1b] = ('const-string/jumbo', 3, 'str')
OPS[0x14] = ('const', 3, 'lit32reg')
OPS[0x15] = ('const/high16', 2, 'lit16reg')
OPS[0x18] = ('const-wide', 5, 'lit64reg')
OPS[0x19] = ('const-wide/high16', 2, 'lit16reg')
for op, nm in [(0x52,'iget'),(0x53,'iget-wide'),(0x54,'iget-object'),(0x55,'iget-boolean'),
               (0x56,'iget-byte'),(0x57,'iget-char'),(0x58,'iget-short'),
               (0x59,'iput'),(0x5a,'iput-wide'),(0x5b,'iput-object'),(0x5c,'iput-boolean'),
               (0x5d,'iput-byte'),(0x5e,'iput-char'),(0x5f,'iput-short'),
               (0xd0,'add-int/lit16'),(0xd1,'rsub-int'),
               (0xd2,'mul-int/lit16'),(0xd3,'div-int/lit16'),
               (0xd8,'add-int/lit8'),(0xd9,'rsub-int/lit8'),(0xda,'mul-int/lit8'),
               (0xdb,'div-int/lit8'),(0xdc,'rem-int/lit8'),(0xdd,'and-int/lit8'),
               (0xde,'or-int/lit8'),(0xdf,'xor-int/lit8'),(0xe0,'shl-int/lit8'),
               (0xe1,'shr-int/lit8'),(0xe2,'ushr-int/lit8')]:
    OPS[op] = (nm, 2, 'field_or_lit')
for op, nm in [(0x44,'aget'),(0x45,'aget-wide'),(0x46,'aget-object'),(0x47,'aget-boolean'),
               (0x48,'aget-byte'),(0x49,'aget-char'),(0x4a,'aget-short'),
               (0x4b,'aput'),(0x4c,'aput-wide'),(0x4d,'aput-object'),(0x4e,'aput-boolean'),
               (0x4f,'aput-byte'),(0x50,'aput-char'),(0x51,'aput-short'),
               (0x60,'sget'),(0x61,'sget-wide'),(0x77-0x14,'x')]:  # placeholder no-op
    if nm == 'x': continue
    OPS[op] = (nm, 2, 'reg2')
for op, nm in [(0x21,'array-length'),(0xb0,'add-int'),(0x90,'add-int/2addr')]:
    OPS[op] = (nm, 1, 'reg2addr')
for op, nm in [(0x2b,'packed-switch'),(0x2c,'sparse-switch')]:
    OPS[op] = (nm, 3, 'payload')
for op, nm in [(0x32,'if-eq'),(0x33,'if-ne'),(0x34,'if-lt'),(0x35,'if-ge'),
               (0x36,'if-gt'),(0x37,'if-le')]:
    OPS[op] = (nm, 2, 'cmp')
for op, nm in [(0x38,'if-eqz'),(0x39,'if-nez'),(0x3a,'if-ltz'),(0x3b,'if-gez'),
               (0x3c,'if-gtz'),(0x3d,'if-lez')]:
    OPS[op] = (nm, 2, 'cmpz')
for op, nm in [(0x74,'invoke-virtual/range'),(0x75,'invoke-super/range'),
               (0x76,'invoke-direct/range'),(0x77,'invoke-static/range'),
               (0x78,'invoke-interface/range')]:
    OPS[op] = (nm, 3, 'range')
# common 2addr arithmetic (only names for readability)
for base, nms in [(0xb0,'add-int'),(0xb1,'sub-int'),(0xb2,'mul-int'),(0xb3,'div-int'),
                  (0xbb,'add-float'),(0xbc,'sub-float'),(0xbd,'mul-float'),(0xbe,'div-float'),
                  (0xca,'add-long'),(0x8f,'int-to-float'),(0x85,'int-to-long'),
                  (0x87,'long-to-float'),(0x8a,'float-to-int')]:
    OPS[base] = (nms+'/2addr', 1, 'reg2addr')
for op, nm in [(0xaf,'sub-int/2addr'),(0x9c,'mul-int/2addr'),(0x9d,'div-int/2addr'),
               (0xa7,'cmp-long'),(0x30,'cmpg-float'),(0x2f,'cmpl-float'),(0x31,'cmpl-double'),
               (0xbf,'sub-long/2addr'),(0x9e,'rem-int/2addr'),(0xdc2,'x')]:
    if nm == 'x': continue
    OPS[op] = (nm+'/2addr', 1, 'reg2addr')
# fill in any unknown 2-op sizes generically below

def disasm(dex, regs, code):
    out = []
    i = 0
    n_units = len(code)//2
    while i < n_units:
        op = code[i*2] | (code[i*2+1] << 8)
        op &= 0xff
        name, sz, kind = OPS.get(op, (f'op-0x{op:02x}', None, '?'))
        if sz is None:
            # infer size: heuristic — most unlisted are 1 or 2; use known families
            if 0x02 <= op <= 0x03 or 0x05 <= op <= 0x06: sz = 2 if op in (0x02,0x05) else 3
            elif 0x7a <= op <= 0x8e or 0x91 <= op <= 0xaf or 0xb4 <= op <= 0xcf: sz = 1
            elif 0xd4 <= op <= 0xd7 or 0xe3 <= op <= 0xff: sz = 2
            else: sz = 1
        raw = code[i*2:(i+sz)*2]
        if kind == 'str':
            idx = struct.unpack_from('<H', raw, 2)[0] if sz >= 2 else 0
            if op == 0x1b:
                idx = struct.unpack_from('<I', raw, 2)[0]
            out.append(f"{i:04d} {name} \"{dex.s(idx)}\"")
        elif kind == 'field_or_lit' and op <= 0x5f:
            try:
                fi = struct.unpack_from('<H', raw, 2)[0]
                c, fn, ft = dex.fid(fi)
                vA = (raw[1] >> 4) & 0xf; vB = raw[1] & 0xf
                out.append(f"{i:04d} {name} v{vA}, v{vB}, {c}.{fn}:{ft}")
            except Exception:
                out.append(f"{i:04d} {name} (field?)")
        elif kind == 'field_or_lit' and 0xd0 <= op <= 0xd7:
            lit = struct.unpack_from('<h', raw, 2)[0]
            vA = raw[1]; vB = raw[3]
            out.append(f"{i:04d} {name} v{vA}, v{vB}, {lit}")
        elif kind == 'field_or_lit' and 0xd8 <= op <= 0xe2:
            vA = raw[1]; vB = raw[2]
            lit = struct.unpack_from('<b', raw, 3)[0]
            out.append(f"{i:04d} {name} v{vA}, v{vB}, {lit}")
        elif kind == 'reg':
            vAA = raw[1]
            out.append(f"{i:04d} {name} v{vAA}")
        elif kind == 'type2':
            ti = struct.unpack_from('<H', raw, 2)[0]
            out.append(f"{i:04d} {name} v{raw[1]}, {dex.t(ti)}")
        elif kind == 'invoke35c':
            mi = struct.unpack_from('<H', raw, 2)[0]
            c, mn, mp = dex.mid(mi)
            cnt = (raw[3] >> 4) & 0xf if sz >= 4 else (raw[1] >> 4) & 0xf
            out.append(f"{i:04d} {name} argc={cnt} {c}.{mn}{mp}")
        elif kind == 'range':
            mi = struct.unpack_from('<H', raw, 2)[0]
            c, mn, mp = dex.mid(mi)
            cnt = raw[1]
            start = struct.unpack_from('<H', raw, 4)[0]
            out.append(f"{i:04d} {name} {{v{start}..v{start+cnt-1}}}, {c}.{mn}{mp}")
        elif kind == 'cmp':
            vA = raw[1] & 0xf; vB = (raw[1] >> 4) & 0xf
            tgt = i + struct.unpack_from('<h', raw, 2)[0]
            out.append(f"{i:04d} {name} v{vA}, v{vB} -> {tgt:04d}")
        elif kind == 'cmpz':
            tgt = i + struct.unpack_from('<h', raw, 2)[0]
            out.append(f"{i:04d} {name} v{raw[1]} -> {tgt:04d}")
        elif kind == 'lit4':
            v = (raw[1] >> 4) & 0xf; r = raw[1] & 0xf
            lit = (raw[0] >> 0)  # const/4: B|A|op — literal in high nibble of byte1
            litv = (raw[1] >> 4) & 0xf
            if litv >= 8: litv -= 16
            out.append(f"{i:04d} {name} v{r}, {litv}")
        elif kind == 'lit16reg':
            lit = struct.unpack_from('<h', raw, 2)[0]
            out.append(f"{i:04d} {name} v{raw[1]}, {lit}")
        elif kind == 'lit32reg':
            lit = struct.unpack_from('<i', raw, 2)[0]
            out.append(f"{i:04d} {name} v{raw[1]}, {lit}")
        elif kind == 'lit64reg':
            lit = struct.unpack_from('<q', raw, 2)[0]
            out.append(f"{i:04d} {name} v{raw[1]}, {lit}")
        elif kind == 'reg2addr':
            vA = raw[1] & 0xf; vB = (raw[1] >> 4) & 0xf
            out.append(f"{i:04d} {name} v{vA}, v{vB}")
        elif kind == 'reg2':
            vA = raw[1] & 0xff; vB = (raw[2] if sz > 1 else 0)
            out.append(f"{i:04d} {name} v{raw[1]}")
        elif kind == 'payload':
            out.append(f"{i:04d} {name} (payload)")
        elif op in (0x2b, 0x2c):
            out.append(f"{i:04d} {name}")
        else:
            out.append(f"{i:04d} {name}")
        i += sz
    return out

def main():
    cls, meth = sys.argv[1], sys.argv[2]
    proto_sub = sys.argv[3] if len(sys.argv) > 3 else None
    z = zipfile.ZipFile(APK)
    dex = Dex(z.read('classes.dex'))
    ms = dex.methods_of(cls)
    if not ms:
        print(f"CLASS NOT FOUND: {cls}"); return
    hits = [m for m in ms if m[0] == meth and (proto_sub is None or proto_sub in m[1])]
    if not hits:
        print(f"--- {cls} methods: {[m[0] for m in ms]}")
        print(f"METHOD NOT FOUND: {cls}.{meth}")
        return
    for (n, p, off, midx) in hits:
        if off == 0:
            print(f"=== {cls}.{meth}{p} abstract/native ==="); continue
        regs, code = dex.read_code(off)
        print(f"=== {cls}.{meth}{p} regs={regs} insns={len(code)//2} ===")
        for line in disasm(dex, regs, code):
            print(" ", line)

if __name__ == '__main__':
    main()
