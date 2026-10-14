#!/usr/bin/env python3
"""cont46_disasm.py — minimal correct DEX class/method disassembler for
CONT-46 Phase-2 static decode. Usage:
  cont46_disasm.py <apk> <Lclass;> [method-name-or-empty] [proto-substr]
Prints every instruction with offset, opcode name, and registers.
"""
import sys, zipfile, struct

def uleb(b, off):
    r = 0; s = 0
    while True:
        by = b[off]; off += 1
        r |= (by & 0x7f) << s
        if not (by & 0x80): break
        s += 7
    return r, off

def sleb(b, off):
    r = 0; s = 0
    while True:
        by = b[off]; off += 1
        r |= (by & 0x7f) << s
        s += 7
        if not (by & 0x80):
            if by & 0x40: r -= (1 << s)
            break
    return r, off

class Dex:
    def __init__(self, data):
        self.b = data
        self.str_off = struct.unpack_from('<I', data, 60)[0]
        self.typ_off = struct.unpack_from('<I', data, 68)[0]
        self.proto_off = struct.unpack_from('<I', data, 76)[0]
        self.fld_off = struct.unpack_from('<I', data, 84)[0]
        self.mth_off = struct.unpack_from('<I', data, 92)[0]
        self.cdef_off = struct.unpack_from('<I', data, 100)[0]
        self.cdef_n = struct.unpack_from('<I', data, 96)[0]
        self.str_n = struct.unpack_from('<I', data, 56)[0]
        self.typ_n = struct.unpack_from('<I', data, 64)[0]
        self.pro_n = struct.unpack_from('<I', data, 72)[0]
        self.fld_n = struct.unpack_from('<I', data, 80)[0]
        self.mth_n = struct.unpack_from('<I', data, 88)[0]
        self._scache = {}

    def s(self, i):
        if i >= self.str_n: raise IndexError(f'string idx {i} >= {self.str_n}')
        if i in self._scache: return self._scache[i]
        data_off = struct.unpack_from('<I', self.b, self.str_off + i*4)[0]
        n, off = uleb(self.b, data_off)
        end = self.b.index(b'\x00', off)
        v = self.b[off:end].decode('utf-8', 'replace')
        self._scache[i] = v
        return v

    def t(self, i): return self.s(struct.unpack_from('<I', self.b, self.typ_off + i*4)[0])

    def _tl_entries(self, params):
        n = struct.unpack_from('<I', self.b, params)[0]
        if n == 0 or n > 256: return []
        u16 = [struct.unpack_from('<H', self.b, params + 4 + k*2)[0] for k in range(n)]
        u32 = [struct.unpack_from('<I', self.b, params + 4 + k*4)[0] for k in range(n)]
        # this repo's runtime dex_parser.cpp:1262-1269 convention reads u16
        # entries; fall back to spec u32 when u16 goes out of range.
        if all(t < self.typ_n for t in u16): return u16
        if all(t < self.typ_n for t in u32): return u32
        return u16

    def proto(self, i):
        if i >= self.pro_n: raise IndexError(f'proto {i} >= {self.pro_n}')
        st, rt, params = struct.unpack_from('<III', self.b, self.proto_off + i*12)
        ps = [self.t(ti) for ti in self._tl_entries(params)] if params else []
        return '(' + ', '.join(ps) + ') -> ' + self.t(rt)

    def meth(self, i):
        if i >= self.mth_n: raise IndexError(f'method idx {i} >= {self.mth_n}')
        cls, proto, name = struct.unpack_from('<HHI', self.b, self.mth_off + i*8)
        return self.t(cls), self.s(name), self.proto(proto)

    def field(self, i):
        cls, typ, name = struct.unpack_from('<HHI', self.b, self.fld_off + i*8)
        return self.t(cls), self.s(name), self.t(typ)

    FIELD_OPS = set(range(0x52, 0x6e))
    TYPE_OPS = {0x1c, 0x1f, 0x20, 0x22, 0x23, 0x24, 0x25}

    def find_class(self, cls):
        for ci in range(self.cdef_n):
            off = self.cdef_off + ci*32
            cls_idx = struct.unpack_from('<I', self.b, off)[0]
            if self.t(cls_idx) == cls:
                return struct.unpack_from('<8I', self.b, off)
        return None

    def methods_of(self, hdr):
        (_c, _a, _sup, _ifs, _sf, _an, class_data_off, _sv) = hdr
        if class_data_off == 0 or class_data_off >= len(self.b):
            return []
        off = class_data_off
        _n1, off = uleb(self.b, off); _n2, off = uleb(self.b, off)
        dm, off = uleb(self.b, off); vm, off = uleb(self.b, off)
        for _ in range(_n1):
            _f, off = uleb(self.b, off); _f, off = uleb(self.b, off)
        for _ in range(_n2):
            _f, off = uleb(self.b, off); _f, off = uleb(self.b, off)
        out = []
        idx = 0
        for _ in range(dm):
            diff, off = uleb(self.b, off); idx += diff
            acc, off = uleb(self.b, off); code, off = uleb(self.b, off)
            out.append(('direct', idx, acc, code))
        idx = 0
        for _ in range(vm):
            diff, off = uleb(self.b, off); idx += diff
            acc, off = uleb(self.b, off); code, off = uleb(self.b, off)
            out.append(('virtual', idx, acc, code))
        return out

    def code(self, code_off):
        b = self.b
        regs, ins, outs, tries, dbg, insns = struct.unpack_from('<HHHHII', b, code_off)
        return regs, ins, outs, code_off + 16, insns  # insns in 16-bit units

# opcode table (name, format) — subset sufficient for support-lib decode
OPS = {
0x00:('nop','10x'),0x01:('move','12x'),0x02:('move/from16','22x'),0x04:('move-wide','12x'),
0x05:('move-wide/from16','22x'),0x07:('move-object','12x'),0x08:('move-object/from16','22x'),
0x0a:('move-result','11x'),0x0b:('move-result-wide','11x'),0x0c:('move-result-object','11x'),
0x0d:('move-exception','11x'),0x0e:('return-void','10x'),0x0f:('return','11x'),
0x10:('return-wide','11x'),0x11:('return-object','11x'),0x12:('const/4','11n'),
0x13:('const/16','21s'),0x14:('const','31i'),0x15:('const/high16','21h'),
0x16:('const-wide/16','21s'),0x17:('const-wide/32','31i'),0x18:('const-wide','51l'),
0x19:('const-wide/high16','21h'),0x1a:('const-string','21c'),0x1b:('const-string/jumbo','31c'),
0x1c:('const-class','21c'),0x1d:('monitor-enter','11x'),0x1e:('monitor-exit','11x'),
0x1f:('check-cast','21c'),0x20:('instance-of','22c'),0x21:('array-length','12x'),
0x22:('new-instance','21c'),0x23:('new-array','22c'),0x24:('filled-new-array','35c'),
0x25:('filled-new-array/range','3rc'),0x26:('fill-array-data','31t'),
0x27:('throw','11x'),0x28:('goto','10t'),0x29:('goto/16','20t'),0x2a:('goto/32','30t'),
0x2b:('packed-switch','31t'),0x2c:('sparse-switch','31t'),
0x2d:('cmpl-float','23x'),0x2e:('cmpg-float','23x'),0x2f:('cmpl-double','23x'),
0x30:('cmpg-double','23x'),0x31:('cmp-long','23x'),
0x32:('if-eq','22t'),0x33:('if-ne','22t'),0x34:('if-lt','22t'),0x35:('if-ge','22t'),
0x36:('if-gt','22t'),0x37:('if-le','22t'),0x38:('if-eqz','21t'),0x39:('if-nez','21t'),
0x3a:('if-ltz','21t'),0x3b:('if-gez','21t'),0x3c:('if-gtz','21t'),0x3d:('if-lez','21t'),
0x44:('aget','23x'),0x46:('aget-object','23x'),0x4b:('aput','23x'),0x4d:('aput-object','23x'),
0x52:('iget','22c'),0x53:('iget-wide','22c'),0x54:('iget-object','22c'),
0x55:('iget-boolean','22c'),0x56:('iget-byte','22c'),0x57:('iget-char','22c'),0x58:('iget-short','22c'),
0x59:('iput','22c'),0x5a:('iput-wide','22c'),0x5b:('iput-object','22c'),
0x5c:('iput-boolean','22c'),0x5d:('iput-byte','22c'),0x5e:('iput-char','22c'),0x5f:('iput-short','22c'),
0x60:('sget','21c'),0x61:('sget-wide','21c'),0x62:('sget-object','21c'),
0x63:('sget-boolean','21c'),0x64:('sget-byte','21c'),0x65:('sget-char','21c'),0x66:('sget-short','21c'),
0x67:('sput','21c'),0x68:('sput-wide','21c'),0x69:('sput-object','21c'),
0x6a:('sput-boolean','21c'),0x6b:('sput-byte','21c'),0x6c:('sput-char','21c'),0x6d:('sput-short','21c'),
0x6e:('invoke-virtual','35c'),0x6f:('invoke-super','35c'),0x70:('invoke-direct','35c'),
0x71:('invoke-static','35c'),0x72:('invoke-interface','35c'),
0x74:('invoke-virtual/range','3rc'),0x75:('invoke-super/range','3rc'),
0x76:('invoke-direct/range','3rc'),0x77:('invoke-static/range','3rc'),
0x78:('invoke-interface/range','3rc'),
0x7b:('int-to-long','12x'),0x7c:('int-to-float','12x'),0x7f:('int-to-byte','12x'),
0x81:('int-to-char','12x'),0x82:('int-to-short','12x'),0x83:('long-to-int','12x'),
0x84:('long-to-float','12x'),0x85:('float-to-int','12x'),0x86:('float-to-long','12x'),
0x87:('double-to-int','12x'),0x8a:('double-to-long','12x'),0x8d:('long-to-double','12x'),
0x90:('add-int','23x'),0x91:('sub-int','23x'),0x92:('mul-int','23x'),0x93:('div-int','23x'),
0x94:('rem-int','23x'),0x95:('add-long','23x'),0x96:('sub-long','23x'),0x97:('mul-long','23x'),
0x9b:('shr-long','23x'),0x9c:('ushr-long','23x'),0x9d:('add-float','23x'),
0x9e:('sub-float','23x'),0x9f:('mul-float','23x'),0xa0:('div-float','23x'),
0xa2:('add-double','23x'),0xa3:('sub-double','23x'),0xa4:('mul-double','23x'),
0xa8:('add-int/2addr','12x'),0xa9:('sub-int/2addr','12x'),0xaa:('mul-int/2addr','12x'),
0xab:('div-int/2addr','12x'),0xac:('rem-int/2addr','12x'),0xad:('add-long/2addr','12x'),
0xaf:('mul-long/2addr','12x'),0xb0:('add-float/2addr','12x'),0xb1:('sub-float/2addr','12x'),
0xb2:('mul-float/2addr','12x'),0xb6:('add-double/2addr','12x'),0xb7:('sub-double/2addr','12x'),
0xb8:('mul-double/2addr','12x'),0xbb:('add-int/lit16','22s'),0xbc:('rsub-int','22s'),
0xbd:('mul-int/lit16','22s'),0xbe:('div-int/lit16','22s'),0xbf:('rem-int/lit16','22s'),
0xc0:('add-int/lit8','22b'),0xc1:('rsub-int/lit8','22b'),0xc2:('mul-int/lit8','22b'),
0xc3:('div-int/lit8','22b'),0xc4:('rem-int/lit8','22b'),0xc5:('and-int/lit8','22b'),
0xc8:('shl-int/lit8','22b'),0xc9:('shr-int/lit8','22b'),0xca:('ushr-int/lit8','22b'),
0xd0:('add-int/lit16-2','22s'),0xdc:('mul-int-lit8','22b'),
0xe3:('undefined-e3','10x'),0xfa:('invoke-polymorphic','45cc'),
}

# format → width in 16-bit code units
FMT_W = {
 '10x':1,'10t':1,'11x':1,'11n':1,'12x':1,
 '20t':2,'21c':2,'21h':2,'21s':2,'21t':2,'22b':2,'22c':2,'22s':2,'22t':2,'22x':2,'23x':2,
 '30t':3,'31c':3,'31i':3,'31t':3,'32x':3,
 '35c':3,'35i':3,'35mi':3,'35ms':3,'35t':3,'3rc':3,'3rm':3,'45cc':3,'51l':3,
 '40sc':4,'41c':4,'5rc':5,
}

def fmt_decode(d, pc, unit, op, base=0):
    b = d.b
    name = OPS.get(op, (f'op-{op:#04x}','?'))[0]
    def reg(n): return f'v{n}'
    if op == 0x00 and unit != 0:
        return f'{name} (pad {unit:#x})'
    f = OPS.get(op, ('?','10x'))[1]
    try:
        if f == '10x': return name
        if f == '12x':
            A = (unit >> 8) & 0xf; B = (unit >> 12) & 0xf
            return f'{name} {reg(A)}, {reg(B)}'
        if f == '11n':
            A = (unit >> 8) & 0xf; Bm = (unit >> 12) & 0xf
            B = Bm if Bm < 8 else Bm - 16
            return f'{name} {reg(A)}, {B}'
        if f == '11x': return f'{name} {reg((unit>>8)&0xff)}'
        if f == '10t':
            offs = (unit>>8)&0xff
            if offs > 127: offs -= 256
            return f'{name} -> {pc+offs:#x}'
        if f == '20t':
            offs = struct.unpack_from('<h', b, base+pc*2+2)[0]
            return f'{name} -> {pc+offs:#x}'
        if f == '22x':
            AA = (unit>>8)&0xff; B = struct.unpack_from('<H', b, base+pc*2+2)[0]
            return f'{name} {reg(AA)}, {reg(B)}'
        if f == '21s':
            AA = (unit>>8)&0xff; B = struct.unpack_from('<h', b, base+pc*2+2)[0]
            return f'{name} {reg(AA)}, {B}'
        if f == '21h':
            AA = (unit>>8)&0xff; B = struct.unpack_from('<h', b, base+pc*2+2)[0] << 16
            return f'{name} {reg(AA)}, {B:#x}'
        if f == '21c':
            AA = (unit>>8)&0xff; B = struct.unpack_from('<H', b, base+pc*2+2)[0]
            if op in d.FIELD_OPS:
                fc, fn, ft = d.field(B)
                return f'{name} {reg(AA)}, {fc}.{fn}:{ft}'
            if op == 0x1a or op == 0x1b:
                return f'{name} {reg(AA)}, "{d.s(B)}"'
            if op in d.TYPE_OPS:
                return f'{name} {reg(AA)}, {d.t(B)}'
            return f'{name} {reg(AA)}, @{B}'
        if f == '21t':
            AA = (unit>>8)&0xff; B = struct.unpack_from('<h', b, base+pc*2+2)[0]
            return f'{name} {reg(AA)}, -> {pc+B:#x}'
        if f == '23x':
            AA = (unit>>8)&0xff; BBCC = struct.unpack_from('<H', b, base+pc*2+2)[0]
            return f'{name} {reg(AA)}, {reg(BBCC&0xff)}, {reg(BBCC>>8)}'
        if f == '22b':
            AA = (unit>>8)&0xff; BBCC = struct.unpack_from('<H', b, base+pc*2+2)[0]
            C = struct.unpack_from('<b', b, base+pc*2+3)[0]
            return f'{name} {reg(AA)}, {reg(BBCC&0xff)}, {C}'
        if f == '22s':
            AA = (unit>>8)&0xff; B = struct.unpack_from('<h', b, base+pc*2+2)[0]
            return f'{name} {reg(AA)}, {reg(B&0xf)}, {B>>4}'
        if f == '22c':
            AA = (unit>>8)&0xff; B = struct.unpack_from('<H', b, base+pc*2+2)[0]
            if op in d.FIELD_OPS:
                fc, fn, ft = d.field(B)
                return f'{name} {reg(AA&0xf)}, {reg(AA>>4)}, {fc}.{fn}:{ft}'
            if op in d.TYPE_OPS:
                return f'{name} {reg(AA&0xf)}, {reg(AA>>4)}, {d.t(B)}'
            return f'{name} {reg(AA&0xf)}, {reg(AA>>4)}, @{B}'
        if f == '22t':
            AA = (unit>>8)&0xff; B = struct.unpack_from('<h', b, base+pc*2+2)[0]
            return f'{name} {reg(AA&0xf)}, {reg(AA>>4)}, -> {pc+B:#x}'
        if f == '30t':
            AA = (unit>>8)&0xff; B = struct.unpack_from('<i', b, base+pc*2+2)[0]
            return f'{name} -> {pc+B:#x}'
        if f == '31i':
            AA = (unit>>8)&0xff; B = struct.unpack_from('<i', b, base+pc*2+2)[0]
            return f'{name} {reg(AA)}, {B}'
        if f == '31t':
            AA = (unit>>8)&0xff; B = struct.unpack_from('<i', b, base+pc*2+2)[0]
            return f'{name} {reg(AA)}, -> {pc+B:#x}'
        if f == '31c':
            AA = (unit>>8)&0xff; B = struct.unpack_from('<I', b, base+pc*2+2)[0]
            return f'{name} {reg(AA)}, @{B} {d.s(B)}'
        if f == '51l':
            AA = (unit>>8)&0xff; B = struct.unpack_from('<q', b, base+pc*2+2)[0]
            return f'{name} {reg(AA)}, {B}'
        if f in ('35c',):
            A = (unit >> 12) & 0xf; G = (unit >> 8) & 0xf
            BBBB = struct.unpack_from('<H', b, base+pc*2+2)[0]
            F = struct.unpack_from('<H', b, base+pc*2+4)[0]
            # F u16 nibbles low→high are C, D, E, F (DEX spec)
            regs = [ (F >> (4*k)) & 0xf for k in range(4) ]  # C D E F
            sel = regs[:A]
            if A == 5: sel.append(G)
            m = d.meth(BBBB)
            return f'{name} {{{", ".join(reg(r) for r in sel)}}}, {m[0]}->{m[1]}:{m[2]}'
        if f == '3rc':
            A = (unit >> 12) & 0xf
            BBBB = struct.unpack_from('<H', b, base+pc*2+2)[0]
            first = struct.unpack_from('<H', b, base+pc*2+4)[0]
            m = d.meth(BBBB)
            rset = f'{{v{first}..v{first+A-1}}}' if A else '{}'
            return f'{name} {rset}, {m[0]}->{m[1]}:{m[2]}'
    except Exception as e:
        return f'{name} <decode-error {e}>'
    return name

def main():
    apk, cls = sys.argv[1], sys.argv[2]
    want_m = sys.argv[3] if len(sys.argv) > 3 else None
    proto_sub = sys.argv[4] if len(sys.argv) > 4 else None
    z = zipfile.ZipFile(apk)
    names = [n for n in z.namelist() if n.endswith('.dex')]
    for dn in names:
        d = Dex(z.read(dn))
        hdr = d.find_class(cls)
        if not hdr: continue
        print(f'## {dn} class {cls}')
        (c, a, sup, _i, _s, _an, _cdo, _sv) = hdr
        print(f'access=0x{a:04x} super={d.t(sup) if sup != 0xFFFFFFFF else "?"}')
        for kind, midx, acc, code in d.methods_of(hdr):
            try:
                mcls, mname, mproto = d.meth(midx)
            except (IndexError, struct.error):
                print(f'  <bad method idx {midx} — class_data walk diverged, skipping>')
                continue
            if want_m and mname != want_m: continue
            if proto_sub and proto_sub not in mproto: continue
            print(f'\n== {kind} {mname}{mproto} access=0x{acc:04x} code_off={code:#x}')
            if code == 0: continue
            regs, ins, outs, base, n = d.code(code)
            print(f'registers={regs} ins={ins} outs={outs} insns={n} units')
            i = 0
            while i < n:
                unit = struct.unpack_from('<H', d.b, base + i*2)[0]
                op = unit & 0xff
                txt = fmt_decode(d, i, unit, op, base)
                fmt = OPS.get(op, ('?', '10x'))[1]
                sz = FMT_W.get(fmt, 1)
                extra = ''
                if op in (0x2b, 0x2c):
                    tgt = struct.unpack_from('<i', d.b, base + i*2 + 2)[0]
                    ident = struct.unpack_from('<H', d.b, base + tgt*2)[0]
                    if ident == 0x0100:
                        psz = struct.unpack_from('<I', d.b, base + tgt*2 + 4)[0]
                        extra = f' (packed payload len={psz})'
                        sz = (tgt + 2 + psz*2) - i   # resume after payload
                    elif ident == 0x0200:
                        psz = struct.unpack_from('<I', d.b, base + tgt*2 + 4)[0]
                        extra = f' (sparse payload len={psz})'
                        sz = (tgt + 2 + psz*4) - i
                print(f'  {i:#06x}: {txt}{extra}')
                i += sz
        return
    print(f'class {cls} NOT FOUND')

if __name__ == '__main__':
    main()
