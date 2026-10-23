#!/usr/bin/env python3
"""cont12_peri_disasm.py — F-NEW-514 decode probe: disassemble methods from
an APK's primary dex with full invoke/const field resolution.
Usage: cont12_peri_disasm.py <apk> <class-desc> [method-name ...]
Prints instructions with pc offsets. Without method names, lists methods."""
import struct, zipfile, sys

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

def sleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        s += 7
        if not (x & 0x80):
            if x & 0x40 and s < 64:
                r |= -(1 << s)
            break
    return r, o

class Dex:
    def __init__(self, data):
        self.d = data
        d = data
        self.str_size, self.str_off = struct.unpack_from('<2I', d, 0x38)
        self.soa = struct.unpack_from(f'<{self.str_size}I', d, self.str_off)
        self.type_size, self.type_off = struct.unpack_from('<2I', d, 0x40)
        self.toa = struct.unpack_from(f'<{self.type_size}I', d, self.type_off)
        self.proto_size, self.proto_off = struct.unpack_from('<2I', d, 0x48)
        self.poa = struct.unpack_from(f'<{self.proto_size}I', d, self.proto_off)
        self.field_size, self.field_off = struct.unpack_from('<2I', d, 0x50)
        self.foa = struct.unpack_from(f'<{self.field_size}I', d, self.field_off)
        self.meth_size, self.meth_off = struct.unpack_from('<2I', d, 0x58)
        self.moa = struct.unpack_from(f'<{self.meth_size}I', d, self.meth_off)
        self.class_size, self.class_off = struct.unpack_from('<2I', d, 0x60)
        self.coa = struct.unpack_from(f'<{self.class_size}I', d, self.class_off)

    def s(self, si):
        off = self.soa[si]
        _, o = uleb(self.d, off)
        return self.d[o:self.d.index(b'\x00', o)].decode('utf-8', 'replace')

    def t(self, ti):
        return self.s(self.toa[ti])

    def proto_sig(self, pi):
        shorty_idx, ret_idx, params_off = struct.unpack_from('<3I', self.d, self.poa[pi])
        ret = self.t(ret_idx)
        ps = []
        if params_off:
            n, o = uleb(self.d, params_off)
            for _ in range(n):
                ti, o = uleb(self.d, o)
                ps.append(self.t(ti))
        return '(' + ''.join(ps) + ')' + ret

    def m(self, mi):
        base = self.moa[mi]
        ci, pi = struct.unpack_from('<2H', self.d, base)
        ni = struct.unpack_from('<I', self.d, base + 4)[0]
        return self.t(ci), self.s(ni), self.proto_sig(pi)

    def f(self, fi):
        base = self.foa[fi]
        cu, ti = struct.unpack_from('<2H', self.d, base)
        ni = struct.unpack_from('<I', self.d, base + 4)[0]
        return self.t(cu), self.t(ti), self.s(ni)

def find_class(dx, cls):
    d = dx.d
    for i in range(dx.class_size):
        off = dx.class_off + i * 32
        cidx, acc, sup, ifs, sdat = struct.unpack_from('<IIIII', d, off)
        if dx.t(cidx) == cls:
            return sdat, acc
    return None, None

def method_code(dx, cls, name_wanted):
    d = dx.d
    sdat, _ = find_class(dx, cls)
    if not sdat:
        return None
    o = sdat
    sf, o = uleb(d, o)
    inf, o = uleb(d, o)
    dm, o = uleb(d, o)
    vm, o = uleb(d, o)
    def read_meths(o, n, direct):
        out = []
        mi = 0
        for _ in range(n):
            di, o = uleb(d, o)
            mi += di
            acc, o = uleb(d, o)
            code_off, o = uleb(d, o)
            mci, mni, mproto = dx.m(mi)
            mname = dx.s(mni)
            if name_wanted is None or mname in name_wanted:
                out.append((mname, mproto, code_off, direct))
        return o, out
    o, direct = read_meths(o, dm, True)
    o, virtual = read_meths(o, vm, False)
    return direct + virtual

def disasm_method(dx, cls, name, proto, code_off):
    d = dx.d
    if not code_off:
        print(f'== {cls}.{name}{proto} (abstract/native, no code)')
        return
    regs, ins, outs, tries, dbg, insns_size = struct.unpack_from('<6H', d, code_off)
    insns_size <<= 1  # 16-bit units -> 16-bit units count already; keep as units
    print(f'== {cls}.{name}{proto} regs={regs} ins={ins} outs={outs} tries={tries} insns_units={insns_size}')
    base = code_off + 16
    u16 = struct.unpack_from(f'<{insns_size}H', d, base)
    code = bytearray()
    for u in u16:
        code += struct.pack('<H', u)
    pc = 0
    while pc < len(code):
        op = code[pc]
        # decode enough to be useful: size in 16-bit units
        def fmt_at(idx):
            try:
                mi = struct.unpack_from('<H', code, idx)[0]
                c, n, p = dx.m(mi)
                return f'{c}.{n}{p}'
            except Exception:
                return f'midx@{idx}?'
        def fld_at(idx):
            try:
                fi = struct.unpack_from('<H', code, idx)[0]
                cu, ty, nm = dx.f(fi)
                return f'{cu}.{nm}:{ty}'
            except Exception:
                return f'fidx@{idx}?'
        def str_at_idx(idx):
            try:
                si = struct.unpack_from('<H', code, idx)[0]
                return repr(dx.s(si))[:80]
            except Exception:
                return f'sidx@{idx}?'
        def ty_at_idx(idx):
            try:
                ti = struct.unpack_from('<H', code, idx)[0]
                return dx.t(ti)
            except Exception:
                return f'tidx@{idx}?'
        def u32_at(off):
            return struct.unpack_from('<I', code, off)[0]
        size = 1
        note = ''
        a = code[pc+1] if pc+1 < len(code) else 0
        if op == 0x00:
            np = code[pc+1]
            if np == 0x00: size = 1
            elif np == 0x01: size = 2
            elif np == 0x02: size = 3
            elif np == 0x03: size = 1
            elif np == 0x04: size = 2
        elif op == 0x01: size = 1; note = f'move v{a}'
        elif op in (0x02,0x03,0x04,0x05,0x06,0x07): size = 1
        elif op == 0x12: size = 1; note = f'const/4 v{a&0xf}, {a>>4 if (a>>4)<8 else (a>>4)-16}'
        elif op == 0x13: size = 2; note = f'const/16 v{a}, {struct.unpack_from("<h", code, pc+2)[0]}'
        elif op == 0x14: size = 3; note = f'const v{a}, {u32_at(pc+2)}'
        elif op == 0x16: size = 2; note = f'const/high16 v{a}, {struct.unpack_from("<H", code, pc+2)[0]}'
        elif op in (0x1a,): size = 2; note = f'const-string v{a}, {str_at_idx(pc+2)}'
        elif op == 0x1b: size = 3; note = f'const-string/jumbo v{a}'
        elif op in (0x1c,): size = 2; note = f'const-class v{a}, {ty_at_idx(pc+2)}'
        elif op in range(0x1d, 0x23): size = 1  # monitor/instance-of family /check-cast 1-2 units
        elif op == 0x1f: size = 2; note = f'instance-of v{a}, {ty_at_idx(pc+2)}'
        elif op == 0x20: size = 2; note = f'check-cast v{a}, {ty_at_idx(pc+2)}'
        elif op in range(0x22, 0x25): size = 2  # new-instance/new-array/filled
        elif op == 0x22: size = 2; note = f'new-instance v{a}, {ty_at_idx(pc+2)}'
        elif op in range(0x52, 0x60):
            size = 2
            kind = 'get' if (op & 1) == 0 else 'put'
            note = f'{kind} {fld_at(pc+2)}'
        elif op in range(0x60, 0x6e):
            size = 2
            kind = 'sget' if (op & 1) == 0 else 'sput'
            note = f'{kind} {fld_at(pc+2)}'
        elif op in (0x6e,0x6f,0x70,0x71,0x72):
            size = 3
            kinds = {0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface'}
            aa = code[pc+1]
            mi = struct.unpack_from('<H', code, pc+2)[0]
            regs_list = [f'v{aa&0xf}']
            g = code[pc+4]
            if aa & 0xf0:
                regs_list = [f'v{(aa>>4)&0xf}', f'v{aa&0xf}']  # not exact; refine below
            # proper: count = aa>>4; regs for counts<=4: FEDC->vC..vG encoding
            cnt = (aa >> 4) & 0xf
            if cnt <= 4:
                rs = []
                if cnt >= 1: rs.append(f'v{a & 0xf}')
                if cnt >= 2: rs.append(f'v{(aa>>4)&0xf}')
                regs_list = rs
            else:
                regs_list = [f'v{struct.unpack_from("<H", code, pc+4)[0] + k}' for k in range(cnt)]
            note = f'{kinds[op]} {fmt_at(pc+2)} args={regs_list}'
        elif op == 0x74 or op in (0x75,0x76,0x77,0x78):
            size = 3
            kinds = {0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',0x77:'invoke-static/range',0x78:'invoke-interface/range'}
            cnt = code[pc+1]
            start = struct.unpack_from('<H', code, pc+4)[0]
            note = f'{kinds[op]} {fmt_at(pc+2)} count={cnt} v{start}..v{start+cnt-1}'
        elif 0x7b <= op <= 0x8f: size = 1
        elif 0x90 <= op <= 0xaf: size = 2
        elif 0xb0 <= op <= 0xcf: size = 1
        elif op in (0xd0,0xd1,0xd2,0xd3,0xd4,0xd5,0xd6,0xd7): size = 2
        elif 0xe3 <= op <= 0xf9: size = 2
        elif op in (0xd8,0xd9,0xda,0xdb,0xdc,0xdd,0xde,0xdf,0xe0,0xe1,0xe2): size = 2
        elif op == 0x28: size = 1; tgt = pc//2 + 1 + struct.unpack_from('<b', code, pc+1)[0]; note = f'goto ->{tgt*2:#06x}'
        elif op == 0x29: size = 2; tgt = pc//2 + 1 + struct.unpack_from('<h', code, pc+2)[0]; note = f'goto/16 ->{tgt*2:#06x}'
        elif op == 0x2a: size = 3; tgt = pc//2 + 1 + struct.unpack_from('<i', code, pc+2)[0]; note = f'goto/32 ->{tgt*2:#06x}'
        elif op in (0x2b,0x2c): size = 3; tgt = pc//2 + 1 + struct.unpack_from('<i', code, pc+2)[0]; note = f'{"packed" if op==0x2b else "sparse"}-switch payload@{tgt*2:#06x}'
        elif op in (0x2d,0x2e,0x2f,0x30,0x31,0x32,0x33,0x34,0x35,0x36,0x37):
            size = 2; tgt = pc//2 + 1 + struct.unpack_from('<h', code, pc+2)[0]; note = f'if-.. ->{tgt*2:#06x}'
        elif op in (0x38,0x39,0x3a,0x3b,0x3c,0x3d):
            size = 3; tgt = pc//2 + 1 + struct.unpack_from('<i', code, pc+2)[0]; note = f'if-../32 ->{tgt*2:#06x}'
        elif op == 0x0a: size = 1
        elif 0x0b <= op <= 0x11: size = 1
        elif op in (0x15,): size = 2
        elif op in (0x17,): size = 2
        elif op in (0x18,): size = 5
        elif op in (0x19,): size = 2
        elif op in (0x1d,0x1e): size = 1
        elif op == 0x21: size = 1
        elif op == 0x23: size = 2
        elif op == 0x24: size = 3; note = 'filled-new-array ' + fmt_at(pc+2)
        elif op == 0x25: size = 3; note = 'filled-new-array/range'
        elif op == 0x26: size = 3
        elif op in (0x27,): size = 1
        print(f'  {pc:#06x}: ' + ' '.join(f'{b:02x}' for b in code[pc:pc+size*2][:8]) + f'  {note}')
        pc += size * 2
    # try blocks
    if tries:
        toff = base + insns_size * 2
        if insns_size % 2: toff += 2
        for i in range(tries):
            su, sp, nh = struct.unpack_from('<3H', d, toff + i*8)
            print(f'  TRY [{su*2:#06x}..{(su+sp)*2:#06x}) handlers={nh}')

def main():
    apk = sys.argv[1]
    cls = sys.argv[2]
    names = set(sys.argv[3:])
    zf = zipfile.ZipFile(apk)
    found = False
    for dn in [n for n in zf.namelist() if n.startswith('classes') and n.endswith('.dex')]:
        dx = Dex(zf.read(dn))
        meths = method_code(dx, cls, names or None)
        if meths is None:
            continue
        found = True
        for (mname, mproto, code_off, direct) in meths:
            if names and mname not in names:
                continue
            disasm_method(dx, cls, mname, mproto, code_off)
        if names:
            break
    if not found:
        print(f'{cls} NOT FOUND', file=sys.stderr)

if __name__ == '__main__':
    main()
