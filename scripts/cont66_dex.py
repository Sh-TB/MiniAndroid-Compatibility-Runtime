#!/usr/bin/env python3
"""cont66_dex.py — parametric DEX disassembler (continuation of cont66_disasm).
Usage: cont66_dex.py <apk> <class-descriptor> <method> [method2 ...]"""
import zipfile, struct, sys

OPCODES = {
    0x00: ('nop', 1), 0x01: ('move', 1), 0x02: ('move/from16', 2),
    0x04: ('move-wide', 1), 0x07: ('move-object', 1), 0x08: ('move-object/from16', 2),
    0x0e: ('return-void', 1), 0x0f: ('return', 1), 0x10: ('return-wide', 1),
    0x11: ('return-object', 1), 0x12: ('const/4', 1), 0x13: ('const/16', 2),
    0x14: ('const', 3), 0x15: ('const/high16', 2), 0x16: ('const-wide/16', 2),
    0x1a: ('const-string', 2), 0x1b: ('const-string/jumbo', 3),
    0x1c: ('const-class', 2), 0x1d: ('monitor-enter', 1), 0x1e: ('monitor-exit', 1),
    0x1f: ('check-cast', 2), 0x20: ('instance-of', 2),
    0x21: ('array-length', 1), 0x22: ('new-instance', 2), 0x23: ('new-array', 2),
    0x24: ('filled-new-array', 3), 0x26: ('filled-new-array/range', 3),
    0x27: ('fill-array-data', 2), 0x28: ('goto', 1), 0x29: ('goto/16', 2),
    0x2a: ('goto/32', 3), 0x2b: ('packed-switch', 3), 0x2c: ('sparse-switch', 3),
    0x2d: ('cmpl-float', 2), 0x2f: ('cmpg-float', 2), 0x31: ('cmpl-double', 2),
    0x32: ('cmp-long', 2), 0x33: ('if-eq', 2), 0x34: ('if-ne', 2),
    0x35: ('if-lt', 2), 0x36: ('if-ge', 2), 0x37: ('if-gt', 2), 0x38: ('if-le', 2),
    0x39: ('if-eqz', 2), 0x3a: ('if-nez', 2), 0x3b: ('if-ltz', 2),
    0x3c: ('if-gez', 2), 0x3d: ('if-gtz', 2), 0x3e: ('if-lez', 2),
    0x44: ('aget-object', 2), 0x4a: ('aget', 2), 0x4b: ('aput', 2),
    0x4c: ('aput-object', 2), 0x4e: ('aput-wide', 2),
    0x51: ('iget-wide', 2), 0x52: ('iget-object', 2), 0x53: ('iget-boolean', 2),
    0x54: ('iget', 2), 0x55: ('iget-object', 2), 0x56: ('iget-boolean', 2),
    0x57: ('iget-byte', 2), 0x58: ('iget-char', 2), 0x59: ('iget-short', 2),
    0x5a: ('iput', 2), 0x5b: ('iput-wide', 2), 0x5c: ('iput-object', 2),
    0x5d: ('iput-boolean', 2), 0x5e: ('iput-byte', 2), 0x5f: ('sget', 2),
    0x60: ('sget-object', 2), 0x61: ('sget-boolean', 2), 0x62: ('sput', 2),
    0x63: ('sput-object', 2), 0x64: ('sput-boolean', 2),
    0x6e: ('invoke-virtual', 3), 0x6f: ('invoke-super', 3),
    0x70: ('invoke-direct', 3), 0x71: ('invoke-static', 3),
    0x72: ('invoke-interface', 3),
    0x74: ('invoke-virtual/range', 3), 0x75: ('invoke-super/range', 3),
    0x76: ('invoke-direct/range', 3), 0x77: ('invoke-static/range', 3),
    0x78: ('invoke-interface/range', 3),
    0x7b: ('int-to-long', 1), 0x81: ('long-to-int', 1),
    0x83: ('int-to-byte', 1), 0x84: ('int-to-char', 1),
    0x85: ('int-to-float', 1), 0x86: ('int-to-double', 1),
    0x87: ('long-to-float', 1), 0x88: ('long-to-double', 1),
    0x8a: ('double-to-int', 1), 0x8e: ('double-to-float', 1),
    0x90: ('add-int', 2), 0x91: ('sub-int', 2), 0x92: ('mul-int', 2),
    0x93: ('div-int', 2), 0x9f: ('int-to-float', 1),
    0xa0: ('add-long', 2), 0xa2: ('mul-long', 2),
    0xaf: ('mul-float', 2), 0xb0: ('add-int/2addr', 1), 0xb1: ('sub-int/2addr', 1),
    0xb2: ('mul-int/2addr', 1), 0xb3: ('div-int/2addr', 1),
    0xbb: ('add-float/2addr', 1), 0xbc: ('sub-float/2addr', 1),
    0xbd: ('div-float/2addr', 1), 0xc0: ('add-long/2addr', 1),
    0xd0: ('add-int/lit16', 2), 0xd1: ('rsub-int', 2),
    0xd8: ('add-int/lit8', 2), 0xd9: ('rsub-int/lit8', 2),
    0xda: ('mul-int/lit8', 2), 0xdb: ('div-int/lit8', 2),
    0xdc: ('or-int/lit8', 2), 0xdd: ('and-int/lit8', 2),
    0xde: ('xor-int/lit8', 2),
    0xe0: ('shl-int/lit8', 2),
}

class Dex:
    def __init__(self, b):
        self.b = b
        self.string_ids_size, self.string_ids_off = struct.unpack_from('<II', b, 0x38)
        self.type_ids_size, self.type_ids_off = struct.unpack_from('<II', b, 0x40)
        self.field_ids_size, self.field_ids_off = struct.unpack_from('<II', b, 0x50)
        self.method_ids_size, self.method_ids_off = struct.unpack_from('<II', b, 0x58)
        self.class_defs_size, self.class_defs_off = struct.unpack_from('<II', b, 0x60)
    def uleb(self, p):
        shift = 0; r = 0
        while True:
            x = self.b[p]; p += 1
            r |= (x & 0x7f) << shift
            if not (x & 0x80): return r, p
            shift += 7
    def string(self, idx):
        off = struct.unpack_from('<I', self.b, self.string_ids_off + 4*idx)[0]
        r, p = self.uleb(off)
        return self.b[p:p+r].decode('utf-8', 'replace')
    def type(self, idx):
        si = struct.unpack_from('<I', self.b, self.type_ids_off + 4*idx)[0]
        return self.string(si)
    def field(self, idx):
        cls_idx, ftype_idx, name_idx = struct.unpack_from('<HHI', self.b, self.field_ids_off + 8*idx)
        return self.type(cls_idx), self.string(name_idx)
    def method(self, idx):
        cls_idx, proto_idx, name_idx = struct.unpack_from('<HHI', self.b, self.method_ids_off + 8*idx)
        return self.type(cls_idx), self.string(name_idx)
    def find_method(self, cls, name):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + 32*i
            cls_idx = struct.unpack_from('<I', self.b, off)[0]
            if self.type(cls_idx) != cls: continue
            cvoff = struct.unpack_from('<I', self.b, off+24)[0]
            if not cvoff: continue
            p = cvoff
            sf, p = self.uleb(p); inf, p = self.uleb(p)
            dm, p = self.uleb(p); vm, p = self.uleb(p)
            for _ in range(sf):
                _, p = self.uleb(p); _, p = self.uleb(p)
            for _ in range(inf):
                _, p = self.uleb(p); _, p = self.uleb(p)
            code_off = 0; prev = 0
            for _ in range(dm):
                di, p = self.uleb(p); a, p = self.uleb(p); co_, p = self.uleb(p)
                prev += di
                cn, mn = self.method(prev)
                if mn == name: code_off = co_
            prev = 0
            for _ in range(vm):
                mi, p = self.uleb(p); a, p = self.uleb(p); co_, p = self.uleb(p)
                prev += mi
                cn, mn = self.method(prev)
                if mn == name: code_off = co_
            if code_off: return code_off
        return None
    def disasm(self, code_off, max_ins=600):
        b = self.b
        insns_size = struct.unpack_from('<I', b, code_off + 12)[0]
        insns_off = code_off + 16
        out = []; p = insns_off; end = insns_off + insns_size*2
        while p < end and len(out) < max_ins:
            op = b[p]
            pc = (p - insns_off) // 2
            if op in OPCODES: name, size = OPCODES[op]
            else: name, size = f'op-{op:#04x}', 1
            try:
                if 0x6e <= op <= 0x72 or 0x74 <= op <= 0x78:
                    midx = struct.unpack_from('<H', b, p+2)[0]
                    cn, mn = self.method(midx)
                    if 0x74 <= op <= 0x78:
                        out.append(f'{pc:4d}: {name} {{v{b[p+1]}..}}, {cn}->{mn}')
                    else:
                        rc = b[p+1]; rg = b[p+2]
                        regs = f'v{rc&0xf},v{(rg>>0)&0xf},v{(rg>>4)&0xf},v{rc>>4}' if size==3 and False else ''
                        if size == 3:
                            regs = f'v{rc&0xf}, v{(rg>>0)&0xf}, v{(rg>>4)&0xf}' + (f', v{rc>>4}' if rc>>4 else '')
                        out.append(f'{pc:4d}: {name} {{{regs}}}, {cn}->{mn}')
                elif op == 0x1a:
                    sidx = struct.unpack_from('<H', b, p+2)[0]
                    out.append(f'{pc:4d}: const-string v{b[p+1]}, "{self.string(sidx)[:70]}"')
                elif op == 0x1b:
                    sidx = struct.unpack_from('<I', b, p+2)[0]
                    out.append(f'{pc:4d}: const-string/jumbo v{b[p+1]}, "{self.string(sidx)[:70]}"')
                elif op == 0x1f:
                    tidx = struct.unpack_from('<H', b, p+2)[0]
                    out.append(f'{pc:4d}: check-cast v{b[p+1]}, {self.type(tidx)}')
                elif op == 0x20:
                    tidx = struct.unpack_from('<H', b, p+2)[0]
                    out.append(f'{pc:4d}: instance-of v{b[p+1]}, {self.type(tidx)}')
                elif op == 0x22:
                    tidx = struct.unpack_from('<H', b, p+2)[0]
                    out.append(f'{pc:4d}: new-instance v{b[p+1]}, {self.type(tidx)}')
                elif 0x51 <= op <= 0x64:
                    fidx = struct.unpack_from('<H', b, p+2)[0]
                    cn, fn = self.field(fidx)
                    out.append(f'{pc:4d}: {name} v{b[p+1]}, {cn}->{fn}')
                elif op in (0x28,):
                    out.append(f'{pc:4d}: goto {(b[p+1] & 0x80 and b[p+1]-256 or b[p+1])}')
                else:
                    out.append(f'{pc:4d}: {name}')
            except Exception as e:
                out.append(f'{pc:4d}: {name} <decode-err {e}>')
            p += size * 2
        return out

def main():
    apk = sys.argv[1]
    cls = sys.argv[2]
    meths = sys.argv[3:]
    z = zipfile.ZipFile(apk)
    for n in sorted(x for x in z.namelist() if x.startswith('classes') and x.endswith('.dex')):
        d = Dex(z.read(n))
        for mn in meths:
            co = d.find_method(cls, mn)
            if co:
                print(f'== {n}: {cls}->{mn} code_off={co:#x}')
                for line in d.disasm(co):
                    print(line)
                return
    print('not found:', cls, meths)

main()
