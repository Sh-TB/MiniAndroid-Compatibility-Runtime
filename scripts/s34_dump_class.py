#!/usr/bin/env python3
"""S34: list all methods/fields of a class in the dooz APK, plus optional
superchain and any other class mentioning a substring (EXP-051 tool family).
Usage: s34_dump_class.py list <Ldesc> | search <name-substr> [limit] | methods <Ldesc>
"""
import sys, zipfile, struct, io

apk = '/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk'

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
        return raw.decode('utf-8', 'replace').rstrip('\x00')
    def t(self, i):
        return self.s(struct.unpack_from('<I', self.data, self.type_o + i*4)[0])
    def classes(self):
        for ci in range(self.cls_n):
            off = self.cls_o + ci*32
            (cidx, acc, sup, ifs, src, an, cdo, sv) = struct.unpack_from('<8I', self.data, off)
            yield cidx, sup, cdo, acc
    def class_name(self, cidx):
        return self.t(cidx)
    def members(self, cdo):
        f = io.BytesIO(self.data); f.seek(cdo)
        sfn = uleb(f); ifn = uleb(f); dmn = uleb(f); vmn = uleb(f)
        sfs = []; fi = 0
        for _ in range(sfn):
            fi += uleb(f); acc = uleb(f)
            fc, ft, fn = struct.unpack_from('<HHI', self.data, self.fid_o + fi*8)
            sfs.append((self.s(fn), self.t(ft)))
        ifs_ = []; fi = 0
        for _ in range(ifn):
            fi += uleb(f); acc = uleb(f)
            fc, ft, fn = struct.unpack_from('<HHI', self.data, self.fid_o + fi*8)
            ifs_.append((self.s(fn), self.t(ft)))
        dms = []; mi = 0
        for _ in range(dmn):
            mi += uleb(f); acc = uleb(f); co = uleb(f)
            mc, mp, mn = struct.unpack_from('<HHI', self.data, self.mid_o + mi*8)
            dms.append((self.s(mn), self.proto(mp), co, acc))
        vms = []; mi = 0
        for _ in range(vmn):
            mi += uleb(f); acc = uleb(f); co = uleb(f)
            mc, mp, mn = struct.unpack_from('<HHI', self.data, self.mid_o + mi*8)
            vms.append((self.s(mn), self.proto(mp), co, acc))
        return sfs, ifs_, dms, vms
    def proto(self, p):
        poff = self.proto_o + p*12
        ret_i = struct.unpack_from('<I', self.data, poff+4)[0]
        po = struct.unpack_from('<I', self.data, poff+8)[0]
        ret = self.t(ret_i); pl = []
        if po:
            n = struct.unpack_from('<I', self.data, po)[0]
            for i in range(n):
                pl.append(self.t(struct.unpack_from('<H', self.data, po+4+i*2)[0]))
        return '(' + ' '.join(pl) + ')->' + ret

OPS = {0x00:'nop',0x0e:'return-void',0x1d:'monitor-enter',0x1e:'monitor-exit',
       0x26:'throw',0x27:'goto',0x01:'move',0x04:'move-wide',0x07:'move-object',
       0x0a:'move-result',0x0b:'move-result-wide',0x0c:'move-result-object',
       0x0d:'move-exception',0x0f:'return',0x10:'return-wide',0x11:'return-object',
       0x12:'const/4',0x21:'array-length',0x02:'move/from16',0x05:'move-wide/from16',
       0x08:'move-object/from16',0x13:'const/16',0x15:'const/high16',0x16:'const-wide/16',
       0x17:'const-wide/32',0x19:'const-wide/high16',0x1c:'const-class',
       0x1f:'check-cast',0x22:'new-instance',0x28:'goto/16',0x37:'if-eqz',0x38:'if-nez',
       0x39:'if-ltz',0x3a:'if-gez',0x3b:'if-gtz',0x3c:'if-lez',0x20:'instance-of',
       0x23:'new-array',0x31:'if-eq',0x32:'if-ne',0x33:'if-lt',0x34:'if-ge',0x35:'if-gt',
       0x36:'if-le',0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',
       0x56:'iget-byte',0x57:'iget-char',0x58:'iget-short',0x59:'iput',0x5a:'iput-wide',
       0x5b:'iput-object',0x5c:'iput-boolean',0x5d:'iput-byte',0x5e:'iput-short',
       0x5f:'iput-char',0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x63:'sget-boolean',
       0x64:'sget-byte',0x65:'sget-char',0x66:'sget-short',0x6a:'sput',0x6b:'sput-wide',
       0x6c:'sput-object',0x6d:'sput-boolean',0x6e:'invoke-virtual',0x6f:'invoke-super',
       0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface',
       0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',
       0x77:'invoke-static/range',0x78:'invoke-interface/range',0x1a:'const-string',
       0x1b:'const-string/jumbo',0x14:'const',0x25:'filled-new-array',0x24:'filled-new-array/range',
       0x2b:'packed-switch',0x2c:'sparse-switch',0x2a:'goto/32',0x29:'goto/16b'}

FMT3 = {0x70, 0x6e, 0x6f, 0x71, 0x72, 0x22, 0x1c, 0x1f}
FMT2 = set(range(0x01,0x0d)) | {0x0f,0x10,0x11,0x12,0x13,0x15,0x16,0x17,0x19,0x1d,0x1e,
        0x20,0x21,0x23,0x27,0x28,0x29,0x2a,0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,
        0x3a,0x3b,0x3c,0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,
        0x5f,0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x6a,0x6b,0x6c,0x6d,0x14,0x15,0x16,0x17}

def disasm(d, code_off, label):
    data = d.data
    (regs, ins, outs, tries, dbg, insns_size) = struct.unpack_from('<HHHHII', data, code_off)
    print(f"{label} regs={regs} ins={ins} outs={outs} insns={insns_size}")
    units = struct.unpack_from(f'<{insns_size}H', data, code_off+16) if insns_size else ()
    i = 0
    while i < insns_size:
        u = units[i]; op = u & 0xff
        name = OPS.get(op, f'op_{op:02x}')
        if op in FMT3: size = 3
        elif op in FMT2: size = 2
        elif op in (0x74,0x75,0x76,0x77,0x78): size = 4
        elif op in (0x2b,0x2c,0x24,0x25): size = 3
        elif op in (0x1a,): size = 2
        elif op in (0x1b,): size = 3
        elif op == 0x18: size = 2
        else: size = 1
        detail = ''
        if name.startswith('invoke') and size >= 3:
            idx = (units[i+1] << 16) | units[i+2] if op < 0x74 else struct.unpack_from('<I', data, code_off+16+(i+1)*2)[0]
            mc, mp, mn = struct.unpack_from('<HHI', data, d.mid_o + idx*8)
            detail = f" {d.t(mc)}.{d.s(mn)}"
        elif name[:4] in ('iget','iput','sget','sput') and size >= 2:
            fid = units[i+1]
            fc, ft, fn = struct.unpack_from('<HHI', data, d.fid_o + fid*8)
            detail = f" {d.t(fc)}.{d.s(fn)}:{d.t(ft)}"
        elif name in ('instance-of','const-class','new-instance','check-cast','new-array') and size >= 2:
            detail = f" {d.t(units[i+1])}"
        elif name in ('const-string','const-string/jumbo') and size >= 2:
            si = units[i+1] if op == 0x1a else struct.unpack_from('<I', data, code_off+16+(i+1)*2)[0]
            detail = f" \"{d.s(si)[:40]}\""
        print(f"  {i:04d}: {name}{detail}")
        i += size

def main():
    mode = sys.argv[1]
    z = zipfile.ZipFile(apk)
    dexes = [Dex(z.read(n)) for n in sorted(z.namelist())
             if n.startswith('classes') and n.endswith('.dex')]
    if mode == 'search':
        sub = sys.argv[2]; lim = int(sys.argv[3]) if len(sys.argv) > 3 else 40
        cnt = 0
        for d in dexes:
            for cidx, sup, cdo, acc in d.classes():
                nm = d.class_name(cidx)
                if sub in nm:
                    supn = d.class_name(sup) if sup else '?'
                    print(f"{nm} extends {supn} (dex)")
                    cnt += 1
                    if cnt >= lim: return
    elif mode == 'bc':
        cls = sys.argv[2]; meth = sys.argv[3]
        pre = sys.argv[4] if len(sys.argv) > 4 else ''
        for d in dexes:
            for cidx, sup, cdo, acc in d.classes():
                if d.class_name(cidx) != cls: continue
                if cdo == 0: continue
                sfs, ifs_, dms, vms = d.members(cdo)
                for n, p, co, a in dms + vms:
                    if n != meth or not co: continue
                    full = p.replace(' ', '')
                    if pre and not full.startswith(pre): continue
                    disasm(d, co, f"{cls}.{n}{p}")
                return
    elif mode in ('methods', 'list'):
        cls = sys.argv[2]
        for d in dexes:
            for cidx, sup, cdo, acc in d.classes():
                if d.class_name(cidx) == cls:
                    supn = d.class_name(sup) if sup else '?'
                    print(f"CLASS {cls} extends {supn}")
                    if cdo == 0:
                        print(" (no class_data)"); return
                    sfs, ifs_, dms, vms = d.members(cdo)
                    for n, t in sfs: print(f"  SF {n}:{t}")
                    for n, t in ifs_: print(f"  IF {n}:{t}")
                    for n, p, co, a in dms: print(f"  DM {n}{p} code=0x{co:x}")
                    for n, p, co, a in vms: print(f"  VM {n}{p} code=0x{co:x}")
                    return
        print("not found:", cls)

if __name__ == '__main__':
    main()
