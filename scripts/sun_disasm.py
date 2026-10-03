#!/usr/bin/env python3
"""sun_disasm.py — clean DEX method disassembler for the Suntimes APK.
Usage: sun_disasm.py <class-descriptor> <method-name> [--all]
"""
import zipfile, struct, io, sys

APK = '/home/z/my-project/tmp/closeout_apks/com.forrestguice.suntimeswidget_135.apk'

z = zipfile.ZipFile(APK)


class Dex:
    def __init__(self, d):
        self.d = d
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
        off = struct.unpack_from('<I', self.d, self.sof + idx * 4)[0]
        f = io.BytesIO(self.d); f.seek(off)
        n = self.uleb(f)
        return f.read(n).rstrip(b'\x00').decode('utf-8', 'replace')

    def type(self, idx):
        di = struct.unpack_from('<I', self.d, self.tof + idx * 4)[0]
        return self.string(di)

    def fields(self):
        for i in range(self.fsz):
            cidx, tidx, nidx = struct.unpack_from('<HHI', self.d, self.fof + i * 8)
            yield i, (self.type(cidx), self.string(nidx), self.type(tidx))

    def methods(self):
        for i in range(self.msz):
            cidx, pidx, nidx = struct.unpack_from('<HHI', self.d, self.mof + i * 8)
            yield i, (self.type(cidx), self.string(nidx), self.proto(pidx))

    def proto(self, idx):
        # proto_id_item: shorty_idx u32, return_type_idx u32, parameters_off u32
        _, ret, poff = struct.unpack_from('<III', self.d, self.pof + idx * 12)
        if poff == 0:
            return self.type(ret) + '()'
        n = struct.unpack_from('<I', self.d, poff)[0]
        ps = [self.type(struct.unpack_from('<H', self.d, poff + 4 + 2 * k)[0]) for k in range(n)]
        return self.type(ret) + '(' + ','.join(ps) + ')'

    def class_data(self, off):
        f = io.BytesIO(self.d); f.seek(off)
        sf = self.uleb(f); inf = self.uleb(f)
        sm = self.uleb(f); vm = self.uleb(f)
        out = {'direct_methods': [], 'virtual_methods': []}
        # encoded_field lists come FIRST: (field_idx_delta, access_flags) pairs
        for _ in range(sf + inf):
            self.uleb(f); self.uleb(f)
        midx = 0; codelast = 0
        for _ in range(sm):
            d = self.uleb(f); midx += d
            acc = self.uleb(f)
            codelast += self.uleb(f)
            out['direct_methods'].append((midx, acc, codelast))
        midx = 0; codelast = 0
        for _ in range(vm):
            d = self.uleb(f); midx += d
            acc = self.uleb(f)
            codelast += self.uleb(f)
            out['virtual_methods'].append((midx, acc, codelast))
        return out

    def code_item(self, off):
        reg, ins, outs, tsz = struct.unpack_from('<HHHH', self.d, off)
        insns_sz = struct.unpack_from('<I', self.d, off + 12)[0]
        insns_off = off + 16
        raw = self.d[insns_off:insns_off + insns_sz * 2]
        return reg, ins, outs, raw


OPNAMES = {
    0x00: 'nop', 0x01: 'move', 0x12: 'const/4', 0x13: 'const/16', 0x14: 'const',
    0x15: 'const/high16', 0x16: 'const-wide/16', 0x18: 'const-wide',
    0x1a: 'const-string', 0x1b: 'const-string/jumbo', 0x1c: 'const-class',
    0x1f: 'check-cast', 0x20: 'instance-of', 0x21: 'array-length',
    0x22: 'new-instance', 0x23: 'new-array', 0x24: 'filled-new-array',
    0x25: 'filled-new-array/range', 0x26: 'fill-array-data',
    0x27: 'throw', 0x28: 'goto', 0x29: 'goto/16', 0x2a: 'goto/32',
    0x2b: 'packed-switch', 0x2c: 'sparse-switch',
    0x2d: 'cmpl-float', 0x2e: 'cmpg-float', 0x2f: 'cmpl-double', 0x30: 'cmpg-double',
    0x31: 'cmp-long',
    0x32: 'if-eq', 0x33: 'if-ne', 0x34: 'if-lt', 0x35: 'if-ge', 0x36: 'if-gt',
    0x37: 'if-le', 0x38: 'if-eqz', 0x39: 'if-nez', 0x3a: 'if-ltz', 0x3b: 'if-gez',
    0x3c: 'if-gtz', 0x3d: 'if-lez',
    0x44: 'aget', 0x45: 'aget-wide', 0x46: 'aget-object', 0x47: 'aget-boolean',
    0x48: 'aget-byte', 0x49: 'aget-char', 0x4a: 'aget-short',
    0x4b: 'aput', 0x4c: 'aput-wide', 0x4d: 'aput-object', 0x4e: 'aput-boolean',
    0x4f: 'aput-byte', 0x50: 'aput-char', 0x51: 'aput-short',
    0x52: 'iget', 0x53: 'iget-wide', 0x54: 'iget-object', 0x55: 'iget-boolean',
    0x56: 'iget-byte', 0x57: 'iget-char', 0x58: 'iget-short',
    0x59: 'iput', 0x5a: 'iput-wide', 0x5b: 'iput-object', 0x5c: 'iput-boolean',
    0x5d: 'iput-byte', 0x5e: 'iput-char', 0x5f: 'iput-short',
    0x60: 'sget', 0x61: 'sget-wide', 0x62: 'sget-object', 0x63: 'sget-boolean',
    0x64: 'sget-byte', 0x65: 'sget-char', 0x66: 'sget-short',
    0x67: 'sput', 0x68: 'sput-wide', 0x69: 'sput-object', 0x6a: 'sput-boolean',
    0x6b: 'sput-byte', 0x6c: 'sput-char', 0x6d: 'sput-short',
    0x6e: 'invoke-virtual', 0x6f: 'invoke-super', 0x70: 'invoke-direct',
    0x71: 'invoke-static', 0x72: 'invoke-interface',
    0x74: 'invoke-virtual/range', 0x75: 'invoke-super/range',
    0x76: 'invoke-direct/range', 0x77: 'invoke-static/range',
    0x78: 'invoke-interface/range',
    0x0b: 'move-result', 0x0c: 'move-result-wide', 0x0a: 'move-result-object',
    0x04: 'move-wide', 0x07: 'move-object', 0x08: 'move-object/16',
    0x0d: 'return-wide', 0x0f: 'return', 0x10: 'return-wide', 0x11: 'return-object',
    0x90: 'add-int', 0x9b: 'sub-long', 0xa0: 'mul-long', 0x84: 'sub-double',
    0xb0: 'add-int/2addr', 0xbb: 'sub-long/2addr', 0xcd: 'mul-double/2addr',
    0xd8: 'add-int/lit8', 0xda: 'sub-int/lit8', 0xdb: 'mul-int/lit8',
    0xdc: 'div-int/lit8', 0xe0: 'and-int/lit8', 0xe1: 'or-int/lit8',
}
INVOKE_OPS = {0x6e, 0x6f, 0x70, 0x71, 0x72}
FIELD_OPS = set(range(0x52, 0x6e))
TYPE_OPS = {0x1c, 0x1f, 0x20, 0x22, 0x23}
LIT8_OPS = set(range(0xd0, 0xe3))  # covers add/sub/mul/div/...-lit8 family


def disasm(dex, raw, method_tbl, field_tbl):
    out = []
    pc = 0
    while pc + 1 < len(raw):
        op = raw[pc]
        name = OPNAMES.get(op, f'op-{op:#04x}')
        if op == 0x00 and pc + 3 < len(raw) and raw[pc + 1] == 0x03 and raw[pc + 2] == 0x00:
            # fill-array-data-payload pseudo
            etw = struct.unpack_from('<H', raw, pc + 4)[0]
            cnt = struct.unpack_from('<I', raw, pc + 6)[0]
            vals = [struct.unpack_from('<h', raw, pc + 10 + 2 * i)[0] for i in range(min(cnt, 24))]
            out.append((pc, f'fill-array-data-payload elem={etw} count={cnt} vals={vals}'))
            pc += 10 + etw // 8 * cnt * 2 if etw else pc + 8
            continue
        if op == 0x26:  # fill-array-data vAA, +BBBBBBBB
            v = raw[pc + 1]
            tgt = pc + struct.unpack_from('<i', raw, pc + 2)[0] * 2
            out.append((pc, f'fill-array-data v{v}, -> {tgt:#x}'))
            pc += 6; continue
        if op == 0x2b or op == 0x2c:
            v = raw[pc + 1]
            tgt = pc + struct.unpack_from('<i', raw, pc + 2)[0] * 2
            out.append((pc, f'{name} v{v}, table@{tgt:#x}'))
            pc += 6; continue
        if op in (0x0a, 0x0b, 0x0c, 0x0f, 0x10, 0x11, 0x1a, 0x1c, 0x1f, 0x20,
                  0x21, 0x22, 0x23, 0x27, 0x28, 0x1b) or op == 0x1d or op == 0x1e:
            if op == 0x1a:
                sidx = struct.unpack_from('<H', raw, pc + 2)[0]
                try: s = dex.string(sidx)
                except Exception: s = '?'
                out.append((pc, f'const-string v{raw[pc+1]}, "{s[:60]}"'))
                pc += 4; continue
            if op in TYPE_OPS:
                tidx = struct.unpack_from('<H', raw, pc + 2)[0]
                try: t = dex.type(tidx)
                except Exception: t = '?'
                out.append((pc, f'{name} v{raw[pc+1]}, {t}'))
                pc += 4; continue
            if op in (0x28,):
                out.append((pc, 'goto')); pc += 2; continue
            out.append((pc, f'{name} v{raw[pc+1]}'))
            pc += 2; continue
        if op == 0x29:
            tgt = pc + struct.unpack_from('<h', raw, pc + 2)[0] * 2
            out.append((pc, f'goto/16 -> {tgt:#x}')); pc += 4; continue
        if op in (0x12,):
            v = raw[pc + 1] & 0xf
            lit = (raw[pc + 1] >> 4) & 0xf
            if lit > 7: lit -= 16
            out.append((pc, f'const/4 v{v}, {lit}')); pc += 2; continue
        if op in (0x13, 0x16):
            v = raw[pc + 1]
            lit = struct.unpack_from('<h', raw, pc + 2)[0]
            out.append((pc, f'{name} v{v}, {lit}')); pc += 4; continue
        if op in (0x14, 0x18):
            v = raw[pc + 1]
            lit = struct.unpack_from('<I', raw, pc + 2)[0]
            out.append((pc, f'{name} v{v}, 0x{lit:08x}')); pc += 6; continue
        if op == 0x15:
            v = raw[pc + 1]
            lit = struct.unpack_from('<H', raw, pc + 2)[0]
            out.append((pc, f'const/high16 v{v}, 0x{lit << 16:08x}')); pc += 4; continue
        if op in (0x32, 0x33, 0x34, 0x35, 0x36, 0x37):
            tgt = pc + struct.unpack_from('<h', raw, pc + 2)[0] * 2
            out.append((pc, f'{name} v{raw[pc+1]}, v{raw[pc+3]}, -> {tgt:#x}'))
            pc += 4; continue
        if op in (0x38, 0x39, 0x3a, 0x3b, 0x3c, 0x3d):
            tgt = pc + struct.unpack_from('<h', raw, pc + 2)[0] * 2
            out.append((pc, f'{name} v{raw[pc+1]}, -> {tgt:#x}'))
            pc += 4; continue
        if op in INVOKE_OPS:
            midx = struct.unpack_from('<H', raw, pc + 2)[0]
            ms = f'method{midx}({dex.d[midx]})'
            try: ms = '{},{},{}'.format(*method_tbl[midx])
            except Exception: pass
            nreg = raw[pc + 1] & 0xf
            regs = [f'v{raw[pc + 4 + i] & 0xf}' for i in range(min(nreg, 5))]
            out.append((pc, f'{name} {{{",".join(regs)}}}, {ms}'))
            pc += 6; continue
        if op in (0x74, 0x75, 0x76, 0x77, 0x78):
            midx = struct.unpack_from('<H', raw, pc + 2)[0]
            try: ms = '{},{},{}'.format(*method_tbl[midx])
            except Exception: ms = f'method{midx}'
            out.append((pc, f'{name}/range v{raw[pc+4]}.., {ms}'))
            pc += 6; continue
        if op in FIELD_OPS:
            fidx = struct.unpack_from('<H', raw, pc + 2)[0]
            try: fs = '{}.{}:{}'.format(*field_tbl[fidx])
            except Exception: fs = f'field{fidx}'
            out.append((pc, f'{name} v{raw[pc+1]}, {fs}'))
            pc += 4; continue
        if op == 0x24:  # filled-new-array {regs}, type
            tidx = struct.unpack_from('<H', raw, pc + 2)[0]
            try: t = dex.type(tidx)
            except Exception: t = '?'
            nreg = raw[pc + 1] & 0xf
            regs = [f'v{raw[pc + 4 + i] & 0xf}' for i in range(min(nreg, 5))]
            out.append((pc, f'filled-new-array {{{",".join(regs)}}}, {t}'))
            pc += 6; continue
        if op == 0x25:
            tidx = struct.unpack_from('<H', raw, pc + 2)[0]
            try: t = dex.type(tidx)
            except Exception: t = '?'
            out.append((pc, f'filled-new-array/range v{raw[pc+4]}.., {t}'))
            pc += 6; continue
        if op in LIT8_OPS:
            v = raw[pc + 1]
            lit = struct.unpack_from('<b', raw, pc + 3)[0]
            out.append((pc, f'{name} v{v}, v{raw[pc+2]}, {lit}'))
            pc += 4; continue
        if op in (0xb0, 0xb1, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6, 0xb7, 0xbb, 0xbd,
                  0xcd, 0xce, 0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97,
                  0x98, 0x99, 0x9a, 0x9b, 0x9c, 0x9d, 0x9e, 0x9f, 0xa0, 0xa1,
                  0xa2, 0xa3, 0xa4, 0xa5, 0xa6, 0xa7, 0xa8, 0xa9, 0xaa, 0xab,
                  0xac, 0xad, 0xae, 0xaf):
            out.append((pc, f'{name} v{raw[pc+1]}, v{raw[pc+2]}'))
            pc += 4; continue
        out.append((pc, f'{name} (raw {raw[pc+1]:02x} {raw[pc+3]:02x}{raw[pc+2]:02x})' if pc + 3 < len(raw) else f'{name} (raw {raw[pc+1]:02x})'))
        pc += 4
    return out


def main():
    want_class = sys.argv[1]
    want_method = sys.argv[2]
    d = Dex(z.read('classes.dex'))
    ftbl = {i: f for i, f in d.fields()}
    mtbl = {i: (c, n, p) for i, (c, n, p) in d.methods()}
    for i in range(d.cds):
        off = d.cdo + i * 32
        cidx, acc = struct.unpack_from('<II', d.d, off)
        icd = struct.unpack_from('<I', d.d, off + 24)[0]
        if cidx >= d.tsz: continue
        try: cname = d.type(cidx)
        except Exception: continue
        if cname != want_class: continue
        cd = d.class_data(icd)
        for lst in ('direct_methods', 'virtual_methods'):
            for mid, macc, co in cd[lst]:
                if mid >= d.msz: continue
                _, mname, mdesc = mtbl[mid]
                if mname != want_method: continue
                print(f'== {cname}.{mname}{mdesc} access={macc:#x} code_off={co:#x}')
                if co == 0:
                    print('   (no code — abstract/native)'); continue
                reg, ins, outs, raw = d.code_item(co)
                print(f'   registers={reg} ins={ins} outs={outs} insns_words={len(raw)//2}')
                for pc, line in disasm(d, raw, mtbl, ftbl):
                    print(f'   {pc:#06x}: {line}')


if __name__ == '__main__':
    main()
