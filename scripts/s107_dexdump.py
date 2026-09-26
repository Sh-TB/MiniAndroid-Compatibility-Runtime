#!/usr/bin/env python3
"""S107 — minimal multi-dex DEX method disassembler (self-contained).
Usage: s107_dexdump.py <apk> <Lclass;> <method> [all]
Prints invoked methods + field ops for the named method across all dex files."""
import sys, zipfile, struct, io

def uleb(f):
    r = 0; s = 0
    while True:
        b = f.read(1)[0]
        r |= (b & 0x7f) << s; s += 7
        if not b & 0x80: break
    return r

class Dex:
    def __init__(self, data, name):
        self.d = data; self.name = name
        self.ssz, self.sof = struct.unpack_from('<II', d := data, 0x38)
        self.tsz, self.tof = struct.unpack_from('<II', d, 0x40)
        self.psz, self.pof = struct.unpack_from('<II', d, 0x48)
        self.fsz, self.fof = struct.unpack_from('<II', d, 0x50)
        self.msz, self.mof = struct.unpack_from('<II', d, 0x58)
        self.cdsz, self.cdof = struct.unpack_from('<II', d, 0x60)

    def string(self, i):
        off = struct.unpack_from('<I', self.d, self.sof + i*4)[0]
        f = io.BytesIO(self.d); f.seek(off)
        n = uleb(f)
        return f.read(n).decode('utf-8', 'replace')

    def type(self, i): return self.string(struct.unpack_from('<I', self.d, self.tof + i*4)[0])

    def proto_shorty(self, i):
        pid, sid, rid = struct.unpack_from('<HHI', self.d, self.pof + i*12)
        return self.string(sid)

    def method(self, i):
        c, p, n = struct.unpack_from('<HHI', self.d, self.mof + i*8)
        return self.type(c), self.string(n), p

    def field(self, i):
        c, t, n = struct.unpack_from('<HHI', self.d, self.fof + i*8)
        return self.type(c), self.string(n), self.type(t)

INVOKE = {0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface'}
INVOKE_R = {0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',0x77:'invoke-static/range',0x78:'invoke-interface/range'}

def decode(dex, code_off):
    d = dex.d
    regsz, insz, outsz, triesz, dbg, insns_sz = struct.unpack_from('<HHHHII', d, code_off)
    insns_off = code_off + 16
    raw = struct.unpack_from('<%dH' % insns_sz, d, insns_off)
    out = []
    pc = 0
    while pc < insns_sz:
        op = raw[pc] & 0xff
        if op in INVOKE:
            aa, meth = (raw[pc] >> 8) | (raw[pc+1] << 8) if False else (raw[pc+1], None)
            # 10x..35c: op AA|BBBB BBBB -> BBBBBB is meth index at pc+1 (16-bit)
            midx = raw[pc+1]
            cls, nm, p = dex.method(midx)
            out.append(f'{pc:5d}: {INVOKE[op]:18s} {cls}->{nm}')
            pc += 3
        elif op in INVOKE_R:
            midx = raw[pc+1]
            cls, nm, p = dex.method(midx)
            out.append(f'{pc:5d}: {INVOKE_R[op]:18s} {cls}->{nm}')
            pc += 3
        elif op in (0x54, 0x59, 0x52, 0x53, 0x55, 0x56, 0x57, 0x58, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f, 0x60, 0x61, 0x62, 0x63):
            fidx = raw[pc+1]
            cls, nm, ft = dex.field(fidx)
            k = {0x54:'iget-object',0x59:'iput-object',0x60:'sget-object',0x61:'sput-object'}.get(op, 'i/sget(%02x)' % op)
            out.append(f'{pc:5d}: {k:18s} {cls}.{nm} : {ft}')
            pc += 2
        elif op == 0x1a:
            sidx = raw[pc+1]
            out.append(f'{pc:5d}: const-string       "{dex.string(sidx)[:60]}"')
            pc += 2
        elif op == 0x1b:
            sidx = (raw[pc+1] | (raw[pc+2] << 16))
            out.append(f'{pc:5d}: const-string/jumbo "{dex.string(sidx)[:60]}"')
            pc += 3
        else:
            pc += 1
    return out

def find_and_dump(apk, cls, meth, show_all=False):
    z = zipfile.ZipFile(apk)
    dexnames = sorted(n for n in z.namelist() if n.endswith('.dex'))
    for dn in dexnames:
        dex = Dex(z.read(dn), dn)
        # find class_def for cls
        found = False
        for c in range(dex.cdsz):
            off = dex.cdof + c*32
            cidx = struct.unpack_from('<I', dex.d, off)[0]
            if dex.type(cidx) != cls: continue
            coff = struct.unpack_from('<I', dex.d, off+24)[0]
            if coff == 0: continue
            f = io.BytesIO(dex.d); f.seek(coff)
            sf = uleb(f); inf = uleb(f); dm = uleb(f); vm = uleb(f)
            fi = 0
            for _ in range(sf): fi += uleb(f); uleb(f)
            for _ in range(inf): fi += uleb(f); uleb(f)
            def emit(mi, code_off):
                nonlocal found
                mcls, mnm, _p = dex.method(mi)
                if mcls != cls: return
                if meth != '*' and mnm != meth: return
                if code_off == 0:
                    print(f'=== {mcls}.{mnm} ({dn}) abstract/native ===')
                    found = True
                    return
                print(f'=== {mcls}.{mnm} ({dn}) ===')
                for line in decode(dex, code_off):
                    print(' ', line)
                print()
                found = True
            mi = 0
            for _ in range(dm):
                diff = uleb(f); mi += diff; acc = uleb(f)
                code_off = uleb(f)
                emit(mi, code_off)
                if found and not show_all: return True
            mi = 0
            for _ in range(vm):
                diff = uleb(f); mi += diff; acc = uleb(f)
                code_off = uleb(f)
                emit(mi, code_off)
                if found and not show_all: return True
        if found and not show_all: return True
    return found

if __name__ == '__main__':
    apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
    show_all = len(sys.argv) > 4
    if not find_and_dump(apk, cls, meth, show_all):
        print(f'NOT FOUND: {cls}.{meth}')
