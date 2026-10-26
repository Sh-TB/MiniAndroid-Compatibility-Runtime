#!/usr/bin/env python3
"""cont41_disasm_regs.py — register-operand Dalvik disassembler (CONT-41 train).

Usage: cont41_disasm_regs.py <apk> <Lcls;> <method>
Prints every instruction with pc, opcode name and FULL register operands
(formats 10t..35c/51l subset used by the engine census APKs). Handles
classes.dex + classes2.dex..N. Method name '*' = dump all methods of class.
"""
import sys, zipfile, struct


class Dex:
    def __init__(self, data):
        self.b = data
        (self.string_ids_size, self.string_ids_off) = struct.unpack_from('<II', data, 0x38)
        (self.type_ids_size, self.type_ids_off) = struct.unpack_from('<II', data, 0x40)
        (self.proto_ids_size, self.proto_ids_off) = struct.unpack_from('<II', data, 0x48)
        (self.field_ids_size, self.field_ids_off) = struct.unpack_from('<II', data, 0x50)
        (self.meth_ids_size, self.meth_ids_off) = struct.unpack_from('<II', data, 0x58)
        (self.class_defs_size, self.class_defs_off) = struct.unpack_from('<II', data, 0x60)

    def u(self, off, n):
        return int.from_bytes(self.b[off:off + n], 'little')

    def uleb(self, off):
        result, shift, off = 0, 0, off
        while True:
            byte = self.b[off]; off += 1
            result |= (byte & 0x7f) << shift
            if not (byte & 0x80): break
            shift += 7
        return result, off

    def sleb(self, off):
        result, shift, off, byte = 0, 0, off, 0
        while True:
            byte = self.b[off]; off += 1
            result |= (byte & 0x7f) << shift
            shift += 7
            if not (byte & 0x80): break
        if byte & 0x40:
            result -= (1 << shift)
        return result, off

    def string(self, idx):
        if idx >= self.string_ids_size: return f"<str{idx}>"
        off = self.u(self.string_ids_off + idx * 4, 4)
        n, off = self.uleb(off)
        raw = self.b[off:off + n]
        return raw.decode('utf-8', 'replace')

    def type(self, idx):
        if idx >= self.type_ids_size: return f"<type{idx}>"
        return self.string(self.u(self.type_ids_off + idx * 4, 4))

    def field(self, idx):
        if idx >= self.field_ids_size: return ("<f>", "<f>", "<f>")
        fo = self.field_ids_off + idx * 8
        cls = self.u(fo, 2); typ = self.u(fo + 2, 2); nam = self.u(fo + 4, 4)
        return (self.type(cls), self.string(nam), self.type(typ))

    def method(self, idx):
        if idx >= self.meth_ids_size: return ("<m>", "<m>", "<m>")
        mo = self.meth_ids_off + idx * 8
        cls = self.u(mo, 2); nam = self.u(mo + 4, 4)
        return (self.type(cls), self.string(nam), self.proto_str(self.u(mo + 2, 2)))

    def proto_str(self, idx):
        po = self.proto_ids_off + idx * 12
        ret = self.u(po + 4, 4)
        poff = self.u(po + 8, 4)
        params = ""
        if poff:
            n = self.u(poff, 4)
            params = "".join(self.type(self.u(poff + 4 + i * 2, 2)) for i in range(n))
        return f"({params}){self.type(ret)}"

    def find_class(self, desc):
        for i in range(self.class_defs_size):
            co = self.class_defs_off + i * 32
            if self.type(self.u(co, 4)) == desc:
                return co
        return None

    def class_methods(self, co):
        return parse_class_data(self, co)


def parse_class_data(d, co):
    """Return (direct_methods, virtual_methods) = list of (name, desc, access, code_off)."""
    off = d.u(co + 24, 4)  # class_data_off in class_def_item
    if not off:
        return [], []
    sf, off = d.uleb(off)
    if_, off = d.uleb(off)
    dm, off = d.uleb(off)
    vm, off = d.uleb(off)
    idx = 0
    for _ in range(sf):
        diff, off = d.uleb(off); idx += diff
        _, off = d.uleb(off)
    idx = 0
    for _ in range(if_):
        diff, off = d.uleb(off); idx += diff
        _, off = d.uleb(off)
    direct, virt = [], []
    idx = 0
    for _ in range(dm):
        diff, off = d.uleb(off); idx += diff
        acc, off = d.uleb(off)
        code_off, off = d.uleb(off)
        mo = d.meth_ids_off + idx * 8
        direct.append((d.string(d.u(mo + 4, 4)), d.proto_str(d.u(mo + 2, 2)), acc, code_off))
    idx = 0
    for _ in range(vm):
        diff, off = d.uleb(off); idx += diff
        acc, off = d.uleb(off)
        code_off, off = d.uleb(off)
        mo = d.meth_ids_off + idx * 8
        virt.append((d.string(d.u(mo + 4, 4)), d.proto_str(d.u(mo + 2, 2)), acc, code_off))
    return direct, virt


def regs_of_invoke(d, o, w, rng):
    """Return the register list of an invoke instruction at byte offset o.
    35c: AG|op BBBB FEDC — count=A, regs = C,D,E,F(,G) in that order.
    3rc: AA|op BBBB CCCC — count=AA(u16@+4), first=CCCC(u16@+6)."""
    if rng:
        size = d.u(o + 4, 2)
        first = d.u(o + 6, 2)
        return f"v{first}..v{first + size - 1}"
    a = (w >> 12) & 0xf  # 35c: A|G|op — count in the HIGH nibble
    if a == 0:
        return ""
    g = (w >> 8) & 0xf   # G = 5th register, low nibble of high byte
    gs = d.u(o + 4, 2)  # FEDC: low nibble = C, high nibble = F
    c = gs & 0xf; dd = (gs >> 4) & 0xf; e = (gs >> 8) & 0xf; f_ = (gs >> 12) & 0xf
    r = [c, dd, e, f_][:a]
    if a == 5:
        r.append(g)  # G from the first code unit
    return ",".join(f"v{x}" for x in r)


REG_OPS_FIELD = {0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f,
                 0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d}
INVOKE_OPS = {0x6e,0x6f,0x70,0x71,0x72}
INVOKE_RANGE = {0x74,0x75,0x76,0x77,0x78}


def fmt(x):
    return f"0x{x:04x}"


def disasm(d, code_off, title):
    insns_size = d.u(code_off + 12, 4)   # u32 @+12 = insns_size (code units)
    insns_off = code_off + 16
    regs = d.u(code_off + 0, 2)          # registers_size u16 @+0
    ins_in = d.u(code_off + 2, 2)        # ins_size u16 @+2
    print(f"== {title}  registers={regs} ins={ins_in} insns={insns_size}")
    pc = 0
    while pc < insns_size:
        o = insns_off + pc * 2
        w = d.u(o, 2)
        op = w & 0xff
        line = f"{fmt(pc)}: "
        if op == 0x00:
            line += "nop"
            pc += 1; print(line); continue
        if op in (0x12,):  # const/4 vA, #+B
            a = (w >> 8) & 0xf; b = (w >> 12) & 0xf
            if b > 7: b -= 16
            line += f"const/4 v{a}, #{b}"
            pc += 1
        elif op in (0x13, 0x16):  # const/16 vAA, #+BBBB
            a = d.b[o + 1]; v = d.u(o + 2, 2)
            if v > 0x7fff: v -= 0x10000
            line += f"{'const/16' if op==0x13 else 'const-wide/16'} v{a}, #{v}"
            pc += 2
        elif op in (0x14, 0x17):  # const vAA, #+BBBBBBBB
            a = d.b[o + 1]; v = d.u(o + 2, 4)
            line += f"{'const' if op==0x14 else 'const-wide'} v{a}, #{v}"
            pc += 3
        elif op == 0x15:  # const/high16
            a = d.b[o + 1]; v = d.u(o + 2, 2)
            line += f"const/high16 v{a}, #{v << 16:#x}"
            pc += 2
        elif op in (0x1a,):  # const-string vAA, string@BBBB
            a = d.b[o + 1]; idx = d.u(o + 2, 2)
            line += f"const-string v{a}, \"{d.string(idx)[:60]}\""
            pc += 2
        elif op == 0x1b:
            a = d.b[o + 1]; idx = d.u(o + 2, 4)
            line += f"const-string/jumbo v{a}, \"{d.string(idx)[:60]}\""
            pc += 3
        elif op == 0x1c:
            a = d.b[o + 1]; idx = d.u(o + 2, 2)
            line += f"const-class v{a}, {d.type(idx)}"
            pc += 2
        elif op in (0x22,):  # new-instance
            a = d.b[o + 1]; idx = d.u(o + 2, 2)
            line += f"new-instance v{a}, {d.type(idx)}"
            pc += 2
        elif op == 0x23:  # new-array vA, vB, type@CCCC
            a = (w >> 8) & 0xf; b = (w >> 12) & 0xf; idx = d.u(o + 2, 2)
            line += f"new-array v{a}, v{b}, {d.type(idx)}"
            pc += 2
        elif op == 0x21:  # array-length vA, vB
            a = (w >> 8) & 0xf; b = (w >> 12) & 0xf
            line += f"array-length v{a}, v{b}"
            pc += 1
        elif op in REG_OPS_FIELD:
            idx = d.u(o + 2, 2)
            a = (w >> 8) & 0xf; b = (w >> 12) & 0xf  # 22c: B|A|op CCCC
            c, n, t = d.field(idx)
            names = {0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',
                     0x56:'iget-byte',0x57:'iget-char',0x58:'iget-short',0x59:'iput',
                     0x5a:'iput-wide',0x5b:'iput-object',0x5c:'iput-boolean',0x5d:'iput-byte',
                     0x5e:'iput-char',0x5f:'iput-short',0x60:'sget',0x61:'sget-wide',
                     0x62:'sget-object',0x63:'sget-boolean',0x64:'sget-byte',0x65:'sget-char',
                     0x66:'sget-short',0x67:'sput',0x68:'sput-wide',0x69:'sput-object',
                     0x6a:'sput-boolean',0x6b:'sput-byte',0x6c:'sput-char',0x6d:'sput-short'}
            if op < 0x60:
                line += f"{names[op]} v{b}, v{a}, {c}.{n}:{t}"
            else:
                line += f"{names[op]} v{b}, {c}.{n}:{t}"
            pc += 2
        elif op in INVOKE_OPS:
            idx = d.u(o + 2, 2)
            c, n, p = d.method(idx)
            names = {0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
                     0x71:'invoke-static',0x72:'invoke-interface'}
            line += f"{names[op]} {{{regs_of_invoke(d, o, w, False)}}}, {c}.{n}{p}"
            pc += 3
        elif op in INVOKE_RANGE:
            idx = d.u(o + 2, 2)
            c, n, p = d.method(idx)
            names = {0x74:'invoke-virtual/range',0x75:'invoke-super/range',
                     0x76:'invoke-direct/range',0x77:'invoke-static/range',
                     0x78:'invoke-interface/range'}
            line += f"{names[op]} {{{regs_of_invoke(d, o, w, True)}}}, {c}.{n}{p}"
            pc += 3
        elif op in (0x28,):  # goto
            off8 = (w >> 8) & 0xff
            if off8 > 127: off8 -= 256
            line += f"goto {fmt(pc + off8)}"
            pc += 1
        elif op == 0x29:
            o16 = d.u(o + 2, 2)
            if o16 > 0x7fff: o16 -= 0x10000
            line += f"goto/16 {fmt(pc + o16)}"
            pc += 2
        elif op == 0x2a:
            o32 = d.u(o + 2, 4)
            if o32 > 0x7fffffff: o32 -= 0x100000000
            line += f"goto/32 {fmt(pc + o32)}"
            pc += 3
        elif 0x32 <= op <= 0x3d:  # if-cmp vA, vB, +CCCC
            names = {0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',
                     0x37:'if-le',0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',
                     0x3c:'if-gtz',0x3d:'if-lez'}
            off16 = d.u(o + 2, 2)
            if off16 > 0x7fff: off16 -= 0x10000
            if op <= 0x37:
                a = (w >> 8) & 0xf; b = (w >> 12) & 0xf
                line += f"{names[op]} v{a}, v{b}, {fmt(pc + off16)}"
            else:
                a = (w >> 8) & 0xf
                line += f"{names[op]} v{a}, {fmt(pc + off16)}"
            pc += 2
        elif 0x0a <= op <= 0x11:  # move-result*
            a = d.b[o + 1]
            names = {0x0a:'move-result',0x0b:'move-result-wide',0x0c:'move-result-object',
                     0x0d:'move-exception',0x0f:'return',0x10:'return-wide',
                     0x11:'return-object',0x0e:'return-void',0x01:'move',
                     0x04:'move-wide',0x07:'move-object'}
            if op in (0x0e,):
                line += "return-void"; pc += 1
            else:
                line += f"{names[op]} v{a}"; pc += 1
        elif op in (0x02, 0x05, 0x08):
            a = d.b[o + 1]; b = d.u(o + 2, 2)
            names = {0x02:'move/from16',0x05:'move-wide/from16',0x08:'move-object/from16'}
            line += f"{names[op]} v{a}, v{b}"; pc += 2
        elif 0xb0 <= op <= 0xcf:
            names = {0xb0:'add-int/2addr',0xb1:'sub-int/2addr',0xb2:'mul-int/2addr',
                     0xb3:'div-int/2addr',0xb4:'rem-int/2addr',0xb5:'and-int/2addr',
                     0xb6:'or-int/2addr',0xb7:'xor-int/2addr',0xb8:'shl-int/2addr',
                     0xb9:'shr-int/2addr',0xba:'ushr-int/2addr',
                     0xc0:'add-long/2addr',0xc1:'sub-long/2addr',0xc2:'mul-long/2addr',
                     0xc3:'div-long/2addr',0xc4:'rem-long/2addr',
                     0xbb:'add-long/2addr',0xbc:'sub-long/2addr',0xbd:'mul-long/2addr',
                     0xbe:'div-long/2addr',0xbf:'rem-long/2addr',
                     0xc5:'ushr-long/2addr',
                     0xa5:'and-long/2addr',0xa6:'or-long/2addr',0xa7:'xor-long/2addr',
                     0xa8:'shl-long/2addr',0xa9:'shr-long/2addr',0xaa:'ushr-long/2addr',
                     0x90:'add-int',0x91:'sub-int',0x92:'mul-int',0x93:'div-int',
                     0x94:'rem-int',0x95:'and-int',0x96:'or-int',0x97:'xor-int',
                     0x98:'shl-int',0x99:'shr-int',0x9a:'ushr-int',
                     0x9b:'add-long',0x9c:'sub-long',0x9d:'mul-long',0x9e:'div-long',
                     0x9f:'rem-long',0xa0:'and-long',0xa1:'or-long',0xa2:'xor-long',
                     0xa3:'shl-long',0xa4:'shr-long',
                     0xb0+0:'add-int/2addr'}
            # 2addr: vA = op vA, vB
            a = (w >> 8) & 0xf; b = (w >> 12) & 0xf
            nm = names.get(op, f'op{op:#04x}')
            line += f"{nm} v{a}, v{b}"; pc += 1
        elif 0xd8 <= op <= 0xe2:  # /lit8
            names = {0xd8:'add-int/lit8',0xd9:'sub-int/lit8',0xda:'mul-int/lit8',
                     0xdb:'div-int/lit8',0xdc:'rem-int/lit8',0xdd:'and-int/lit8',
                     0xde:'or-int/lit8',0xdf:'xor-int/lit8',0xe0:'shl-int/lit8',
                     0xe1:'shr-int/lit8',0xe2:'ushr-int/lit8'}
            a = d.b[o + 1]; b = (w >> 12) & 0xf; c = d.b[o + 3]
            if c > 127: c -= 256
            line += f"{names[op]} v{a}, v{b}, #{c}"; pc += 2
        elif 0xd0 <= op <= 0xd7:  # /lit16
            names = {0xd0:'add-int/lit16',0xd1:'sub-int/lit16',0xd2:'mul-int/lit16',
                     0xd3:'div-int/lit16',0xd4:'rem-int/lit16',0xd5:'and-int/lit16',
                     0xd6:'or-int/lit16',0xd7:'xor-int/lit16'}
            a = d.b[o + 1]; b = (w >> 12) & 0xf; c = d.u(o + 2, 2)
            if c > 0x7fff: c -= 0x10000
            line += f"{names[op]} v{a}, v{b}, #{c}"; pc += 2
        elif 0x7b <= op <= 0x8f:  # unary 12x
            names = {0x7b:'neg-int',0x7c:'not-int',0x7d:'neg-long',0x7e:'not-long',
                     0x7f:'neg-float',0x80:'neg-double',0x81:'int-to-long',
                     0x82:'int-to-float',0x83:'int-to-double',0x84:'long-to-int',
                     0x85:'long-to-float',0x86:'long-to-double',0x87:'float-to-int',
                     0x88:'float-to-long',0x89:'float-to-double',0x8a:'double-to-int',
                     0x8b:'double-to-long',0x8c:'double-to-float',0x8d:'int-to-byte',
                     0x8e:'int-to-char',0x8f:'int-to-short'}
            a = (w >> 8) & 0xf; b = (w >> 12) & 0xf
            line += f"{names[op]} v{a}, v{b}"; pc += 1
        elif op == 0x27:  # throw
            a = (w >> 8) & 0xf
            line += f"throw v{a}"; pc += 1
        elif op in (0x1d, 0x1e):
            a = d.b[o + 1]
            line += f"{'monitor-enter' if op==0x1d else 'monitor-exit'} v{a}"; pc += 1
        elif op in (0x44,0x45,0x46,0x47,0x48,0x49,0x4a,0x4b,0x4c,0x4d,0x4e,0x4f,0x50,0x51):
            names = {0x44:'aget',0x45:'aget-wide',0x46:'aget-object',0x47:'aget-boolean',
                     0x48:'aget-byte',0x49:'aget-char',0x4a:'aget-short',0x4b:'aput',
                     0x4c:'aput-wide',0x4d:'aput-object',0x4e:'aput-boolean',0x4f:'aput-byte',
                     0x50:'aput-char',0x51:'aput-short'}
            a = d.b[o + 1]; b = d.b[o + 2]  # 23x: vAA, vBB(array), vCC(index)
            line += f"{names[op]} v{a}, v{b}"; pc += 2
        elif op in (0x90,0x91,0x92,0x93,0x94,0x95,0x96,0x97,0x98,0x99,0x9a,
                    0x9b,0x9c,0x9d,0x9e,0x9f,0xa0,0xa1,0xa2,0xa3,0xa4,0xa5,0xa6,0xa7,
                    0xa8,0xa9,0xaa):
            names = {0x90:'add-int',0x91:'sub-int',0x92:'mul-int',0x93:'div-int',
                     0x94:'rem-int',0x95:'and-int',0x96:'or-int',0x97:'xor-int',
                     0x98:'shl-int',0x99:'shr-int',0x9a:'ushr-int',
                     0x9b:'add-long',0x9c:'sub-long',0x9d:'mul-long',0x9e:'div-long',
                     0x9f:'rem-long',0xa0:'and-long',0xa1:'or-long',0xa2:'xor-long',
                     0xa3:'shl-long',0xa4:'shr-long',0xa5:'ushr-long'}
            a = d.b[o + 1]
            bb = d.b[o + 2]; cc = d.b[o + 3]
            nm = names.get(op, f'op{op:#04x}')
            line += f"{nm} v{a}, v{bb}, v{cc}"; pc += 2
        elif op in (0x24,0x25):
            idx = d.u(o + 2, 2)
            c, n, p = d.method(idx)
            line += f"{'filled-new-array' if op==0x24 else 'filled-new-array/range'} {c}.{n}{p}"
            pc += 3
        elif op == 0x26:
            idx = d.u(o + 2, 4)
            line += f"fill-array-data (payload@{idx})"
            pc += 3
        else:
            line += f"op{op:#04x}"
            # size table fallback
            if op in (0x03,): pc += 2
            elif op in (0x18,): pc += 5
            elif op in (0x19,): pc += 2
            elif op in (0x2b,0x2c): pc += 3
            elif 0xb0 <= op <= 0xcf: pc += 1
            else: pc += 2
        print(line)


def main():
    apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
    if not cls.endswith(';'): cls += ';'
    z = zipfile.ZipFile(apk)
    for name in [n for n in z.namelist() if n.endswith('.dex')]:
        d = Dex(z.read(name))
        co = d.find_class(cls)
        if co is None: continue
        direct, virt = parse_class_data(d, co)
        for kind, lst in (("direct", direct), ("virtual", virt)):
            for (n, p, acc, code_off) in lst:
                if meth != '*' and n != meth: continue
                if not code_off: continue
                disasm(d, code_off, f"{cls}.{n}{p} [{name} {kind}]")


if __name__ == "__main__":
    main()
