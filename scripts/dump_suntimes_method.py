#!/usr/bin/env python3
"""dump_suntimes_method.py — disassemble a method from the Suntimes APK
(ALL dex files scanned) to locate the exact NPE instruction."""
import sys, zipfile, struct, io

APK = '/tmp/f084_probe.apk'
WANT_CLASS = sys.argv[1] if len(sys.argv) > 1 else 'Lnet/time4j/PlainDate;'
WANT_METHOD = sys.argv[2] if len(sys.argv) > 2 else 'registerUnits'

class Dex:
    def __init__(self, data):
        self.data = data
        d = data
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
        raw = f.read(n)
        return raw.rstrip(b'\x00').decode('utf-8', 'replace')

    def typeid(self, idx):
        off = struct.unpack_from('<I', self.data, self.tof + idx*4)[0]
        return struct.unpack_from('<I', self.data, off)[0]

    def fields(self):
        for i in range(self.fsz):
            off = self.fof + i*8
            cid, tidx = struct.unpack_from('<II', self.data, off)
            yield i, self.string(self.string(cid)), self.string(self.typeid(tidx))

    def methods(self):
        for i in range(self.msz):
            off = self.mof + i*8
            cid, pidx = struct.unpack_from('<II', self.data, off)
            yield i, self.string(self.string(cid)), self.string(self.typeid(pidx))

    def class_data(self, cd_off):
        f = io.BytesIO(self.data); f.seek(cd_off)
        sf, inf, dm, vm = (self.uleb(f) for _ in range(4))
        out = {'static_fields': [], 'direct_methods': [], 'virtual_methods': []}
        fid = 0
        for _ in range(sf):
            fid += self.uleb(f); acc = self.uleb(f)
            out['static_fields'].append((fid, acc))
        iid = 0
        for _ in range(inf):
            iid += self.uleb(f); acc = self.uleb(f)
            out['static_fields'].append((iid, acc))
        mid = 0
        for _ in range(dm):
            mid += self.uleb(f); acc = self.uleb(f); co = self.uleb(f)
            out['direct_methods'].append((mid, acc, co))
        for _ in range(vm):
            mid += self.uleb(f); acc = self.uleb(f); co = self.uleb(f)
            out['virtual_methods'].append((mid, acc, co))
        return out

    def code_item(self, off):
        reg, ins, outs, tries, dbg, insns = struct.unpack_from('<HHHHII', self.data, off)
        size = insns * 2
        raw = self.data[off+16: off+16+size]
        return reg, ins, outs, raw

OPNAMES = {0x00:'nop',0x01:'move',0x04:'move-wide',0x07:'move-object',0x0a:'move-result',0x0b:'move-result-wide',0x0c:'move-result-object',0x0d:'move-exception',0x0e:'return-void',0x0f:'return',0x10:'return-wide',0x11:'return-object',0x12:'const/4',0x13:'const/16',0x14:'const',0x15:'const/high16',0x16:'const-wide/16',0x17:'const-wide/32',0x18:'const-wide',0x19:'const-wide/high16',0x1a:'const-string',0x1b:'const-string-jumbo',0x1c:'const-class',0x1d:'monitor-enter',0x1e:'monitor-exit',0x1f:'check-cast',0x20:'instance-of',0x21:'array-length',0x22:'new-instance',0x23:'new-array',0x24:'filled-new-array',0x25:'filled-new-array/range',0x26:'fill-array-data',0x27:'throw',0x28:'goto',0x29:'goto/16',0x2a:'goto/32',0x2b:'packed-switch',0x2c:'sparse-switch',0x2d:'cmpl-float',0x2e:'cmpg-float',0x2f:'cmpl-double',0x30:'cmpg-double',0x31:'cmp-long',0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',0x37:'if-le',0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez',0x44:'aget',0x45:'aget-wide',0x46:'aget-object',0x47:'aget-boolean',0x48:'aget-byte',0x49:'aget-char',0x4a:'aget-short',0x4b:'aput',0x4c:'aput-wide',0x4d:'aput-object',0x4e:'aput-boolean',0x4f:'aput-byte',0x50:'aput-char',0x51:'aput-short',0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',0x56:'iget-byte',0x57:'iget-char',0x58:'iget-short',0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',0x5c:'iput-boolean',0x5d:'iput-byte',0x5e:'iput-char',0x5f:'iput-short',0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x63:'sget-boolean',0x64:'sget-byte',0x65:'sget-char',0x66:'sget-short',0x67:'sput',0x68:'sput-wide',0x69:'sput-object',0x6a:'sput-boolean',0x6b:'sput-byte',0x6c:'sput-char',0x6d:'sput-short',0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface',0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',0x77:'invoke-static/range',0x78:'invoke-interface/range'}

def disasm(dex, raw):
    out = []
    pc = 0
    while pc < len(raw):
        op = raw[pc]
        name = OPNAMES.get(op, f'op-{op:#04x}')
        if op == 0x12:  # const/4
            b = raw[pc+1]
            out.append((pc, f'{name} v{b & 0xf}, {((b>>4)^0x8)-0x8 if b>>4 & 0x8 else b>>4}'))
            pc += 2; continue
        if op in (0x13, 0x16):  # const/16, const-wide/16
            v = struct.unpack_from('<h', raw, pc+2)[0]
            areg = raw[pc+1] & 0xff if op == 0x13 else struct.unpack_from('<B', raw, pc+1)[0] & 0xf
            out.append((pc, f'{name} v{raw[pc+1]}, {v}'))
            pc += 4; continue
        if op == 0x14 or op == 0x17:
            v = struct.unpack_from('<i', raw, pc+2)[0]
            out.append((pc, f'{name} v{raw[pc+1]}, {v}'))
            pc += 6; continue
        if op == 0x15:
            v = struct.unpack_from('<H', raw, pc+2)[0]
            out.append((pc, f'{name} v{raw[pc+1]}, 0x{v << 16:08x}'))
            pc += 4; continue
        if op == 0x1a:  # const-string
            sidx = struct.unpack_from('<H', raw, pc+2)[0]
            try: s = dex.string(sidx)
            except Exception: s = '?'
            out.append((pc, f'const-string v{raw[pc+1]}, "{s[:40]}"'))
            pc += 4; continue
        if op in (0x22, 0x1c, 0x1f, 0x20, 0x23, 0x24):
            tidx = struct.unpack_from('<H', raw, pc+2)[0]
            try: t = dex.string(dex.typeid(tidx))
            except Exception: t = '?'
            out.append((pc, f'{name} v{raw[pc+1]}, {t}'))
            pc += 4; continue
        if op in (0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f,0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d):
            fidx = struct.unpack_from('<H', raw, pc+2)[0]
            try:
                # field id: first uleb-less lookup: field_ids[i] = (class_idx u16, type_idx u16, name_idx u32)
                off = dex.fof + fidx*8
                cidx, tidx, nidx = struct.unpack_from('<HHI', dex.data, off)
                fs = f'{dex.string(dex.typeid(cidx))}.{dex.string(nidx)}:{dex.string(dex.typeid(tidx))}'
            except Exception as e: fs = f'field{fidx}({e})'
            out.append((pc, f'{name} v{raw[pc+1]}, {fs}'))
            pc += 4; continue
        if op in (0x6e,0x6f,0x70,0x71,0x72):
            midx = struct.unpack_from('<H', raw, pc+2)[0]
            try:
                off = dex.mof + midx*8
                cidx, pidx = struct.unpack_from('<HH', dex.data, off)
                ms = f'{dex.string(dex.typeid(cidx))}.{dex.string(pidx)}'
            except Exception as e: ms = f'method{midx}({e})'
            nreg = raw[pc+1] & 0xf
            regs = [f'v{raw[pc+4+i] & 0xf}' for i in range(min(nreg,4))]
            out.append((pc, f'{name} {{{",".join(regs)}}}, {ms}'))
            pc += 6; continue
        if op in (0x74,0x75,0x76,0x77,0x78):
            midx = struct.unpack_from('<H', raw, pc+2)[0]
            try:
                off = dex.mof + midx*8
                cidx, pidx = struct.unpack_from('<HH', dex.data, off)
                ms = f'{dex.string(dex.typeid(cidx))}.{dex.string(pidx)}'
            except Exception: ms = f'method{midx}'
            out.append((pc, f'{name}/range v{raw[pc+4]}.., {ms}'))
            pc += 6; continue
        if op in (0x28,):
            out.append((pc, f'goto {((raw[pc+1]^0x80)-0x80 if raw[pc+1]&0x80 else raw[pc+1])}'))
            pc += 2; continue
        if op in (0x38,0x39,0x3a,0x3b,0x3c,0x3d):
            off = struct.unpack_from('<h', raw, pc+2)[0]
            out.append((pc, f'{name} v{raw[pc+1]}, +{off} (->{pc+off*2})'))
            pc += 4; continue
        if op in (0x0e,):
            out.append((pc, 'return-void')); pc += 2; continue
        # generic 2-unit
        out.append((pc, f'{name} (raw {raw[pc+1]:02x} {raw[pc+3]:02x}{raw[pc+2]:02x})'))
        pc += 4
    return out

z = zipfile.ZipFile(APK)
for n in sorted(x for x in z.namelist() if x.endswith('.dex')):
    d = Dex(z.read(n))
    # find class def for WANT_CLASS
    for i in range(d.cds):
        off = d.cdo + i*32
        cidx, acc = struct.unpack_from('<II', d.data, off)
        icd = struct.unpack_from('<I', d.data, off+24)[0]
        if cidx >= d.tsz: continue
        try: cname = d.string(d.typeid(cidx))
        except Exception: continue
        if cname != WANT_CLASS: continue
        cd = d.class_data(icd)
        allm = list(d.methods())
        for lst in ('direct_methods','virtual_methods'):
            for mid, acc, co in cd[lst]:
                _, mname, mdesc = allm[mid]
                if mname != WANT_METHOD: continue
                print(f'== {cname}.{mname}{mdesc} access={acc:#x} code_off={co:#x} dex={n}')
                if co == 0:
                    print('   (no code — abstract/native)'); continue
                reg, ins, outs, raw = d.code_item(co)
                print(f'   registers={reg} ins={ins}')
                for pc, line in disasm(d, raw):
                    marker = ' <<<< NPE pc' if pc == 0x2e or pc == 0x2f else ''
                    print(f'   {pc:#06x}: {line}{marker}')
