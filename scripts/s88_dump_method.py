#!/usr/bin/env python3
"""S88 generic DEX method dumper — disassemble named methods from an APK's DEX."""
import sys, zipfile, struct, io

def uleb128(f):
    r = 0; s = 0
    while True:
        b = f.read(1)[0]
        r |= (b & 0x7f) << s
        s += 7
        if not b & 0x80: break
    return r

class Dex:
    def __init__(self, path):
        z = zipfile.ZipFile(path)
        names = [n for n in z.namelist() if n.endswith('.dex')]
        self.dexes = []
        for n in names:
            self.dexes.append((n, z.read(n)))
        self.cur = None
        self.cur_name = ''
        self.parse()

    def parse(self):
        pass

    def load(self, i):
        self.cur_name, self.data = self.dexes[i]
        d = self.data
        self.ssz, self.sof = struct.unpack_from('<II', d, 0x38)
        self.tsz, self.tof = struct.unpack_from('<II', d, 0x40)
        self.psz, self.pof = struct.unpack_from('<II', d, 0x48)
        self.fsz, self.fof = struct.unpack_from('<II', d, 0x50)
        self.msz, self.mof = struct.unpack_from('<II', d, 0x58)

    def string(self, idx):
        off = struct.unpack_from('<I', self.data, self.sof + idx*4)[0]
        f = io.BytesIO(self.data); f.seek(off)
        n = uleb128(f)
        return f.read(n).decode('utf-8', 'replace')

    def type_desc(self, idx):
        return self.string(struct.unpack_from('<I', self.data, self.tof + idx*4)[0])

    def find_method(self, cls, name):
        for i in range(len(self.dexes)):
            self.load(i)
            f = io.BytesIO(self.data); f.seek(self.mof)
            for _ in range(self.msz):
                m = struct.unpack_from('<HHIII', self.data, self.mof + _*16)
                # method_id: class_idx(u16) proto_idx(u16) name_idx(u32)
                mid_off = self.mof + _*16
                class_idx, proto_idx, name_idx = struct.unpack_from('<HHI', self.data, mid_off)
                if self.string(name_idx) == name and self.type_desc(class_idx) == cls:
                    return (i, class_idx, name_idx)
        return None

    # find method code via class_data
    def dump(self, cls, name):
        hit = self.find_method(cls, name)
        if not hit:
            print('NOT FOUND', cls, name); return
        di, class_idx, name_idx = hit
        # locate class_def for cls
        for c in range(self.cds if hasattr(self,'cds') else 0):
            pass
        cdsz, cdof = struct.unpack_from('<II', self.data, 0x60)
        for c in range(cdsz):
            off = cdof + c*32
            cidx = struct.unpack_from('<I', self.data, off)[0]
            if cidx != class_idx: continue
            coff = struct.unpack_from('<I', self.data, off+24)[0]
            if coff == 0:
                print('no class_data'); return
            f = io.BytesIO(self.data); f.seek(coff)
            sf = uleb128(f); inf = uleb128(f); dm = uleb128(f); vm = uleb128(f)
            # skip static fields
            fi = 0
            for _ in range(sf):
                fi += uleb128(f); uleb128(f)
            for _ in range(inf):
                fi += uleb128(f); uleb128(f)
            for _ in range(dm):
                diff = uleb128(f); acc = uleb128(f)
                mi = fi; fi += 1
                code_off = uleb128(f)   # ALWAYS read to keep stream in sync
                mid_off = self.mof + mi*16
                cidx2, pidx, nidx = struct.unpack_from('<HHI', self.data, mid_off)
                if self.string(nidx) != name: continue
                if code_off == 0: print('abstract'); return
                self.dump_code(code_off, di, cidx2, nidx)
                return
        print('class_data miss')

    def dump_code(self, code_off, di, cls_idx, name_idx):
        d = self.data
        regsz, insz, outsz, triesz, dbg, insns_sz, insns_off = struct.unpack_from('<HHHHIII', d, code_off)
        print(f'=== {self.type_desc(cls_idx)}.{self.string(name_idx)} (dex {di} {self.cur_name}) regs={regsz} ins={insz} outs={outsz} insns={insns_sz}')
        pc = 0
        units = insns_sz
        raw = struct.unpack_from('<%dH' % units, d, insns_off)
        while pc < units:
            op = raw[pc] & 0xFF
            # minimal decode: 1-3 units of hex + opcode name
            sz = {0x00:1}.get(op)
            if op in (0x12,0x13,0x1a): sz = 2
            elif op in (0x22,0x6e,0x6f,0x70,0x71,0x72,0x1b,0x1c,0x54,0x59,0x70): sz = 3
            elif op in (0x2b,0x2c,0x26): sz = 3
            elif op == 0x0e or (0x0a <= op <= 0x0d) or (0x04 <= op <= 0x08): sz = 1
            elif op in (0x74,0x75,0x76,0x77,0x78): sz = 3
            else: sz = 1
            words = ' '.join('%04x' % raw[pc+i] for i in range(sz) if pc+i < units)
            NAMES = {0x22:'new-instance',0x70:'invoke-direct',0x6e:'invoke-virtual',0x6f:'invoke-super',0x71:'invoke-static',0x72:'invoke-interface',0x74:'invoke-virtual/range',0x77:'invoke-interface/range',0x76:'invoke-static/range',0x11:'return-object',0x0f:'return',0x54:'iget-object',0x59:'iput-object',0x0a:'move-result',0x0c:'move-result-object',0x12:'const/4',0x13:'const/16',0x1a:'const-string',0x1b:'const-string/jumbo',0x1c:'const-class'}
            nm = NAMES.get(op, 'op%02x' % op)
            print(f'  {pc:4d}: {nm:22s} {words}')
            pc += sz

if __name__ == '__main__':
    apk = sys.argv[1]
    cls = sys.argv[2]
    meth = sys.argv[3]
    d = Dex(apk)
    d.dump(cls, meth)
