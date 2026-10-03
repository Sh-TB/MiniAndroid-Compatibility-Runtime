#!/usr/bin/env python3
"""S117 — multi-DEX method dumper for the OFFICIAL Telegram APK.
Usage: s117_dump_official.py <Lclass;> <method_name> [method_name ...]
Dumps matching methods from every classes*.dex with raw Dalvik disassembly
(opcode + registers + string/field/method operands)."""
import sys, zipfile, struct, io, os

APK = '/home/z/my-project/upload/tg/telegram_official.apk'

OPC = {
 0x00:('nop',0),0x01:('move',1),0x02:('move/from16',1),0x03:('move/16',1),
 0x04:('move-wide',1),0x05:('move-wide/from16',1),0x06:('move-wide/16',1),
 0x07:('move-object',1),0x08:('move-object/from16',1),0x09:('move-object/16',1),
 0x0a:('move-result',1),0x0b:('move-result-wide',1),0x0c:('move-result-object',1),
 0x0d:('move-exception',1),0x0e:('return-void',0),0x0f:('return',1),
 0x10:('return-wide',1),0x11:('return-object',1),0x12:('const/4',1),
 0x13:('const/16',1),0x14:('const',1),0x15:('const/high16',1),0x16:('const-wide/16',1),
 0x17:('const-wide/32',1),0x18:('const-wide',1),0x19:('const-wide/high16',1),
 0x1a:('const-string',1),0x1b:('const-string/jumbo',1),0x1c:('const-class',1),
 0x1d:('monitor-enter',1),0x1e:('monitor-exit',1),0x1f:('check-cast',1),
 0x20:('instance-of',1),0x21:('array-length',1),0x22:('new-instance',1),
 0x23:('new-array',1),0x24:('filled-new-array',1),0x25:('filled-new-array/range',1),
 0x26:('fill-array-data',1),0x27:('throw',1),0x28:('goto',1),0x29:('goto/16',1),
 0x2a:('goto/32',1),0x2b:('packed-switch',1),0x2c:('sparse-switch',1),
 0x2d:('cmpl-float',1),0x2e:('cmpg-float',1),0x2f:('cmpl-double',1),0x30:('cmpg-double',1),
 0x31:('cmp-long',1),0x32:('if-eq',1),0x33:('if-ne',1),0x34:('if-lt',1),0x35:('if-ge',1),
 0x36:('if-gt',1),0x37:('if-le',1),0x38:('if-eqz',1),0x39:('if-nez',1),0x3a:('if-ltz',1),
 0x3b:('if-gez',1),0x3c:('if-gtz',1),0x3d:('if-lez',1),
 0x44:('aget',1),0x45:('aget-wide',1),0x46:('aget-object',1),0x47:('aget-boolean',1),
 0x48:('aget-byte',1),0x49:('aget-char',1),0x4a:('aget-short',1),
 0x4b:('aput',1),0x4c:('aput-wide',1),0x4d:('aput-object',1),0x4e:('aput-boolean',1),
 0x4f:('aput-byte',1),0x50:('aput-char',1),0x51:('aput-short',1),
 0x52:('iget',1),0x53:('iget-wide',1),0x54:('iget-object',1),0x55:('iget-boolean',1),
 0x56:('iget-byte',1),0x57:('iget-char',1),0x58:('iget-short',1),
 0x59:('iput',1),0x5a:('iput-wide',1),0x5b:('iput-object',1),0x5c:('iput-boolean',1),
 0x5d:('iput-byte',1),0x5e:('iput-char',1),0x5f:('iput-short',1),
 0x60:('sget',1),0x61:('sget-wide',1),0x62:('sget-object',1),0x63:('sget-boolean',1),
 0x64:('sget-byte',1),0x65:('sget-char',1),0x66:('sget-short',1),
 0x67:('sput',1),0x68:('sput-wide',1),0x69:('sput-object',1),0x6a:('sput-boolean',1),
 0x6b:('sput-byte',1),0x6c:('sput-char',1),0x6d:('sput-short',1),
 0x6e:('invoke-virtual',1),0x6f:('invoke-super',1),0x70:('invoke-direct',1),
 0x71:('invoke-static',1),0x72:('invoke-interface',1),
 0x74:('invoke-virtual/range',1),0x75:('invoke-super/range',1),0x76:('invoke-direct/range',1),
 0x77:('invoke-static/range',1),0x78:('invoke-interface/range',1),
 0x7b:('neg-int',1),0x7c:('not-int',1),0x7d:('neg-long',1),0x7e:('not-long',1),
 0x7f:('neg-float',1),0x80:('neg-double',1),0x81:('int-to-long',1),0x82:('int-to-float',1),
 0x83:('int-to-double',1),0x84:('long-to-int',1),0x85:('long-to-float',1),
 0x86:('long-to-double',1),0x87:('float-to-int',1),0x88:('float-to-long',1),
 0x89:('float-to-double',1),0x8a:('double-to-int',1),0x8b:('double-to-long',1),
 0x8c:('double-to-float',1),0x8d:('int-to-byte',1),0x8e:('int-to-char',1),0x8f:('int-to-short',1),
 0x90:('add-int',1),0x91:('sub-int',1),0x92:('mul-int',1),0x93:('div-int',1),
 0x94:('rem-int',1),0x95:('and-int',1),0x96:('or-int',1),0x97:('xor-int',1),
 0x98:('shl-int',1),0x99:('shr-int',1),0x9a:('ushr-int',1),
 0x9b:('add-long',1),0x9c:('sub-long',1),0x9d:('mul-long',1),0x9e:('div-long',1),
 0x9f:('rem-long',1),0xa0:('and-long',1),0xa1:('or-long',1),0xa2:('xor-long',1),
 0xa3:('shl-long',1),0xa4:('shr-long',1),0xa5:('ushr-long',1),
 0xa6:('add-float',1),0xa7:('sub-float',1),0xa8:('mul-float',1),0xa9:('div-float',1),
 0xaa:('rem-float',1),0xab:('add-double',1),0xac:('sub-double',1),0xad:('mul-double',1),
 0xae:('div-double',1),0xaf:('rem-double',1),
 0xb0:('add-int/2addr',1),0xb1:('sub-int/2addr',1),0xb2:('mul-int/2addr',1),
 0xb3:('div-int/2addr',1),0xb4:('rem-int/2addr',1),0xb5:('and-int/2addr',1),
 0xb6:('or-int/2addr',1),0xb7:('xor-int/2addr',1),0xb8:('shl-int/2addr',1),
 0xb9:('shr-int/2addr',1),0xba:('ushr-int/2addr',1),
 0xbb:('add-long/2addr',1),0xbc:('sub-long/2addr',1),0xbd:('mul-long/2addr',1),
 0xbe:('div-long/2addr',1),0xbf:('rem-long/2addr',1),0xc0:('and-long/2addr',1),
 0xc1:('or-long/2addr',1),0xc2:('xor-long/2addr',1),0xc3:('shl-long/2addr',1),
 0xc4:('shr-long/2addr',1),0xc5:('ushr-long/2addr',1),
 0xc6:('add-float/2addr',1),0xc7:('sub-float/2addr',1),0xc8:('mul-float/2addr',1),
 0xc9:('div-float/2addr',1),0xca:('rem-float/2addr',1),
 0xcb:('add-double/2addr',1),0xcc:('sub-double/2addr',1),0xcd:('mul-double/2addr',1),
 0xce:('div-double/2addr',1),0xcf:('rem-double/2addr',1),
 0xd0:('add-int/lit16',1),0xd1:('rsub-int',1),0xd2:('mul-int/lit16',1),
 0xd3:('div-int/lit16',1),0xd4:('rem-int/lit16',1),0xd5:('and-int/lit16',1),
 0xd6:('or-int/lit16',1),0xd7:('xor-int/lit16',1),0xd8:('add-int/lit8',1),
 0xd9:('rsub-int/lit8',1),0xda:('mul-int/lit8',1),0xdb:('div-int/lit8',1),
 0xdc:('rem-int/lit8',1),0xdd:('and-int/lit8',1),0xde:('or-int/lit8',1),
 0xdf:('xor-int/lit8',1),0xe0:('shl-int/lit8',1),0xe1:('shr-int/lit8',1),
 0xe2:('ushr-int/lit8',1),
}

# opcode sizes in 16-bit code units (2 = format 20/21/22/23/35x/3x, etc.)
def op_units(op):
    if op in (0x00,0x0e,0x27,0x28,0x29,0x38,0x39,0x3a,0x3b,0x3c,0x3d,
              0x7b,0x7c,0x7d,0x7e,0x7f,0x80,0x81,0x82,0x83,0x84,0x85,0x86,0x87,0x88,
              0x89,0x8a,0x8b,0x8c,0x8d,0x8e,0x8f,0x1d,0x1e): return 1
    if op in (0x02,0x05,0x08,0x12,0x13,0x15,0x16,0x17,0x19,0x1f,0x21,0x22,0x23,
              0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x44,0x45,0x46,0x47,0x48,0x49,0x4a,
              0x4b,0x4c,0x4d,0x4e,0x4f,0x50,0x51,0x52,0x53,0x54,0x55,0x56,0x57,0x58,
              0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f,0x60,0x61,0x62,0x63,0x64,0x65,0x66,
              0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d,0x6b,0x90,0x91,0x92,0x93,0x94,0x95,
              0x96,0x97,0x98,0x99,0x9a,0x9b,0x9c,0x9d,0x9e,0x9f,0xa0,0xa1,0xa2,0xa3,
              0xa4,0xa5,0xa6,0xa7,0xa8,0xa9,0xaa,0xab,0xac,0xad,0xae,0xaf,
              0xd0,0xd2,0xd3,0xd4,0xd5,0xd6,0xd7,0xd8,0xda,0xdb,0xdc,0xdd,0xde,0xdf,
              0xdf,0xe0,0xe1,0xe2,0xb0,0xb1,0xb2,0xb3,0xb4,0xb5,0xb6,0xb7,0xb8,0xb9,
              0xba,0xbb,0xbc,0xbd,0xbe,0xbf,0xc0,0xc1,0xc2,0xc3,0xc4,0xc5,0xc6,0xc7,
              0xc8,0xc9,0xca,0xcb,0xcc,0xcd,0xce,0xcf): return 2
    if op in (0x2a,): return 3
    if op in (0x01,0x04,0x07,0x11,0x10,0x0f,0x0a,0x0b,0x0c,0x0d,0x14,0x18,
              0x1a,0x1c,0x20,0x6e,0x6f,0x70,0x71,0x72,0x24,0x25,
              0xd1,): return 3
    if op in (0x1b,0x26,0x2b,0x2c,0x74,0x75,0x76,0x77,0x78): return 3
    return 2  # conservative default

class Dex:
    def __init__(self, name, data):
        self.name = name
        self.data = data
        d = self.data
        self.ssz, self.sof = struct.unpack_from('<II', d, 0x38)
        self.tsz, self.tof = struct.unpack_from('<II', d, 0x40)
        self.psz, self.pof = struct.unpack_from('<II', d, 0x48)
        self.fsz, self.fof = struct.unpack_from('<II', d, 0x50)
        self.msz, self.mof = struct.unpack_from('<II', d, 0x58)
        self.cds, self.cdo = struct.unpack_from('<II', d, 0x60)

    def uleb(self, off):
        r = 0; s = 0
        while True:
            b = self.data[off]; off += 1
            r |= (b & 0x7f) << s; s += 7
            if not b & 0x80: break
        return r, off

    def string(self, idx):
        off = struct.unpack_from('<I', self.data, self.sof + idx*4)[0]
        n, off = self.uleb(off)
        return self.data[off:off+n].decode('utf-8', errors='replace')

    def type(self, idx):
        return self.string(struct.unpack_from('<I', self.data, self.tof + idx*4)[0])

    def proto(self, idx):
        shy, rt, ps = struct.unpack_from('<HIH', self.data, self.pof + idx*12)
        return self.type(rt)

    def method_sig(self, midx):
        mc, mp, mn = struct.unpack_from('<HHI', self.data, self.mof + midx*8)
        name = self.string(mn)
        return name

    def field_name(self, fidx):
        fc, ft, fn = struct.unpack_from('<HHI', self.data, self.fof + fidx*8)
        return self.string(fn)

    def methods_of_class(self, cls):
        """cls: 'Lcom/x/Y;' -> list of (name, code_off, dex)."""
        out = []
        d = self.data
        for i in range(self.cds):
            off = self.cdo + i*32
            tidx = struct.unpack_from('<I', d, off)[0]
            if self.type(tidx) != cls: continue
            co = struct.unpack_from('<I', d, off + 24)[0]  # class_data_off
            if co == 0: continue
            # class_data_item counts are uleb128
            sf, co = self.uleb(co)
            inf, co = self.uleb(co)
            dm, co = self.uleb(co)
            vm, co = self.uleb(co)
            # encoded_field: uleb128 field_idx_diff, uleb128 access_flags
            for j in range(sf):
                _, co = self.uleb(co)
                _, co = self.uleb(co)
            for j in range(inf):
                _, co = self.uleb(co)
                _, co = self.uleb(co)
            for kind in range(2):
                cnt = dm if kind == 0 else vm
                moff = 0
                for j in range(cnt):
                    moff, co = self.uleb(co)  # method_idx_diff
                    _, co = self.uleb(co)      # access_flags
                    cdoff, co = self.uleb(co)  # code_off
                    midx = moff if j == 0 else midx_prev + moff
                    # method_ids entry: class_idx u16, proto u16, name u32
                    _, _, nidx = struct.unpack_from('<HHI', d, self.mof + midx*8)
                    out.append((self.string(nidx), cdoff))
                    midx_prev = midx
        return out

def disasm(dex, name, code_off, maxn=200):
    d = dex.data
    if code_off == 0: return f'  (abstract/native)'
    regs, ins, outs, tries, dbg, insn_size = struct.unpack_from('<HHHHII', d, code_off)
    out = [f'  registers={regs} ins={ins} outs={outs} insns={insn_size}']
    pc = 0
    base = code_off + 16
    while pc < insn_size and maxn > 0:
        maxn -= 1
        u = struct.unpack_from('<H', d, base + pc*2)[0]
        op = u & 0xff
        aa = (u >> 8) & 0xff
        nm = OPC.get(op, f'op_{op:02x}')[0]
        extra = ''
        u2 = struct.unpack_from('<H', d, base + pc*2 + 2)[0] if pc+1 < insn_size else 0
        u3 = struct.unpack_from('<H', d, base + pc*2 + 4)[0] if pc+2 < insn_size else 0
        try:
            if op in (0x1a,0x1b):
                extra = f' "{dex.string(aa & 0xffff if op==0x1a else (aa | (u2<<16)))[:70]}"'
            elif op in (0x1c,0x1f,0x20,0x22):
                extra = f' {dex.type(aa | ((u2 & 0xff) << 16)) if op in (0x1f,) else dex.type((aa | (u2<<16)) & 0xffffffff)}'
                if op == 0x1c: extra = f' {dex.type(aa)}'
                if op == 0x22: extra = f' {dex.type(aa | (u2 << 16) if False else (aa & 0xff) | ((u2 & 0xff00) << 8))}'
            elif 0x52 <= op <= 0x6d:
                idx = (aa & 0xff) | ((u2 & 0xff) << 8)
                extra = f' {dex.field_name(idx)}'
            elif op in (0x6e,0x6f,0x70,0x71,0x72):
                idx = (aa & 0xff) | ((u2 & 0xff) << 8)
                mc, mp, mn = struct.unpack_from('<HHI', d, dex.mof + idx*8)
                extra = f' {dex.type(mc)}.{dex.string(mn)}'
            elif op in (0x74,0x75,0x76,0x77,0x78):
                mc, mp, mn = struct.unpack_from('<HHI', d, dex.mof + u2*8)
                extra = f' {dex.type(mc)}.{dex.string(mn)}'
        except Exception as e:
            extra = f' <err {e}>'
        out.append(f'  {pc:4d}: {nm:<24} a={aa:<3} {extra}')
        pc += op_units(op)
    return '\n'.join(out)

def main():
    cls = sys.argv[1]
    names = set(sys.argv[2:])
    z = zipfile.ZipFile(APK)
    dexes = sorted(n for n in z.namelist() if n.endswith('.dex') and n.startswith('classes'))
    for dn in dexes:
        dex = Dex(dn, z.read(dn))
        ms = dex.methods_of_class(cls)
        if not ms: continue
        print(f'=== {cls} in {dn} ===')
        for name, coff in ms:
            if names and name not in names: continue
            print(f'--- .{name} code_off={coff}')
            print(disasm(dex, name, coff))

if __name__ == '__main__':
    main()

