#!/usr/bin/env python3
"""cont66_disasm.py — minimal DEX method disassembler for the OpenCalc
keyDigitPadMappingToDisplay decode (CONT-66 W2)."""
import zipfile, struct, sys

APK = '/home/z/my-project/upload/opencalculator_53.apk'
CLASSES = ['classes.dex', 'classes2.dex', 'classes3.dex']
TARGET_CLS = 'Lcom/darkempire78/opencalculator/activities/MainActivity;'
TARGET_METH = sys.argv[1] if len(sys.argv) > 1 else 'keyDigitPadMappingToDisplay'

class Dex:
    def __init__(self, b):
        self.b = b
        self.string_ids_size, self.string_ids_off = struct.unpack_from('<II', b, 0x38)
        self.type_ids_size, self.type_ids_off = struct.unpack_from('<II', b, 0x40)
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
            sf, p = self.uleb(p)
            inf, p = self.uleb(p)
            dm, p = self.uleb(p)
            vm, p = self.uleb(p)
            for _ in range(sf):
                _, p = self.uleb(p); _, p = self.uleb(p)
            for _ in range(inf):
                _, p = self.uleb(p); _, p = self.uleb(p)
            acc = 0
            prev = 0
            code_off = 0
            for _ in range(dm):
                di, p = self.uleb(p); a, p = self.uleb(p)
                co_, p = self.uleb(p); prev += di
                cn, mn = self.method(prev)
                if mn == name: code_off = co_
            prev = 0
            for _ in range(vm):
                mi, p = self.uleb(p); a, p = self.uleb(p)
                co_, p = self.uleb(p); prev += mi
                cn, mn = self.method(prev)
                if mn == name: code_off = co_
            if code_off: return code_off
        return None

    def _code_off(self, midx):
        # scan method_ids → find the encoded_method with this index? Instead:
        # we already have code_off from the walk in find_method — this helper
        # is unused; code_off handled inline.
        return 0

    def disasm(self, code_off, max_ins=400):
        b = self.b
        insns_size, insns_off = struct.unpack_from('<I', b, code_off + 12)[0], code_off + 16
        out = []
        p = insns_off
        end = insns_off + insns_size * 2
        while p < end and len(out) < max_ins:
            op = b[p]
            pc = (p - insns_off) // 2
            name, size = OPCODES.get(op, (f'op-{op:#04x}', 1))
            if name.startswith('invoke-') and op not in (0x6e,):
                pass
            if 0x6e <= op <= 0x72:  # invoke-kind
                midx = struct.unpack_from('<H', b, p+2)[0]
                cn, mn = self.method(midx)
                regs = [b[p+1]] + [b[p+2+i] for i in range(size-2)] if size <= 4 else []
                if size == 3:
                    regs = [b[p+1], b[p+2]]
                elif size == 4:
                    regs = [b[p+1], b[p+2], b[p+3]]
                out.append(f'{pc:4d}: {name} {{{",".join(map(str,regs))}}}, {cn}->{mn}')
            elif op in (0x74, 0x75, 0x76, 0x77, 0x78):  # invoke-kind/range
                midx = struct.unpack_from('<H', b, p+2)[0]
                cn, mn = self.method(midx)
                out.append(f'{pc:4d}: {name} {{v{b[p+1]}..}}, {cn}->{mn}')
            elif op == 0x1a:  # const-string
                sidx = struct.unpack_from('<H', b, p+2)[0]
                out.append(f'{pc:4d}: const-string v{b[p+1]}, "{self.string(sidx)[:60]}"')
            elif op == 0x1b:  # const-string/jumbo
                sidx = struct.unpack_from('<I', b, p+2)[0]
                out.append(f'{pc:4d}: const-string/jumbo v{b[p+1]}, "{self.string(sidx)[:60]}"')
            elif op == 0x55 or op == 0x54:  # iget/iput-object? (54=iget-object)
                midx = struct.unpack_from('<H', b, p+2)[0]
                # field_ids
                field_ids_off = struct.unpack_from('<I', b, 0x54)[0]
                cls_idx, ftype_idx, name_idx = struct.unpack_from('<HHI', b, field_ids_off + 8*midx)
                out.append(f'{pc:4d}: {name} v{b[p+1]}, {self.type(cls_idx)}->{self.string(name_idx)}')
            elif op in (0x59, 0x5a, 0x5b, 0x5c, 0x5f, 0x60):
                midx = struct.unpack_from('<H', b, p+2)[0]
                field_ids_off = struct.unpack_from('<I', b, 0x54)[0]
                cls_idx, ftype_idx, name_idx = struct.unpack_from('<HHI', b, field_ids_off + 8*midx)
                out.append(f'{pc:4d}: {name} {"v"+str(b[p+1])}, {self.type(cls_idx)}->{self.string(name_idx)}')
            else:
                out.append(f'{pc:4d}: {name}')
            p += size * 2
        return out

OPCODES = {
    0x00: ('nop', 1), 0x01: ('move', 1), 0x0e: ('return-void', 1),
    0x0f: ('return', 1), 0x11: ('return-object', 1), 0x12: ('const/4', 1),
    0x13: ('const/16', 2), 0x14: ('const', 3), 0x1a: ('const-string', 2),
    0x1b: ('const-string/jumbo', 3), 0x1c: ('const-class', 2),
    0x21: ('array-length', 1), 0x22: ('new-instance', 2), 0x23: ('new-array', 2),
    0x28: ('goto', 1), 0x29: ('goto/16', 2), 0x2a: ('goto/32', 3),
    0x2b: ('packed-switch', 3), 0x2c: ('sparse-switch', 3),
    0x35: ('if-ge', 2), 0x33: ('if-eq', 2), 0x34: ('if-ne', 2), 0x36: ('if-gt', 2),
    0x37: ('if-le', 2), 0x38: ('if-eqz', 2), 0x39: ('if-nez', 2),
    0x3a: ('if-ltz', 2), 0x3b: ('if-gez', 2), 0x3c: ('if-gtz', 2), 0x3d: ('if-lez', 2),
    0x54: ('iget-object', 2), 0x55: ('iget', 2), 0x56: ('iget-boolean', 2),
    0x57: ('iget-byte', 2), 0x58: ('iget-char', 2), 0x59: ('iput', 2),
    0x5a: ('iput-object', 2), 0x5b: ('iput-boolean', 2), 0x5c: ('iput-char', 2),
    0x5f: ('sget', 2), 0x60: ('sget-object', 2), 0x61: ('sget-boolean', 2),
    0x62: ('sput', 2), 0x63: ('sput-object', 2), 0x64: ('sput-boolean', 2),
    0x6e: ('invoke-virtual', 3), 0x6f: ('invoke-super', 3),
    0x70: ('invoke-direct', 3), 0x71: ('invoke-static', 3),
    0x72: ('invoke-interface', 3),
    0x74: ('invoke-virtual/range', 3), 0x76: ('invoke-direct/range', 3),
    0x77: ('invoke-static/range', 3), 0x78: ('invoke-interface/range', 3),
    0x0a: ('move-result', 1), 0x0c: ('move-result-object', 1),
    0x90: ('add-int', 2), 0xa00 & 0xff: ('?', 1),
    0x91: ('sub-int', 2), 0x92: ('mul-int', 2), 0x93: ('div-int', 2),
    0x9f: ('int-to-float', 1), 0xb0: ('add-int/2addr', 1), 0xb1: ('sub-int/2addr', 1),
    0xb2: ('mul-int/2addr', 1), 0xb3: ('div-int/2addr', 1),
    0xbb: ('add-float/2addr', 1), 0xbc: ('sub-float/2addr', 1),
    0xbd: ('div-float/2addr', 1), 0xc0: ('add-long/2addr', 1),
    0xc9: ('int-to-long', 1), 0xd0: ('add-int/lit16', 2),
    0xd1: ('rsub-int', 2), 0xd8: ('add-int/lit8', 2), 0xd9: ('rsub-int/lit8', 2),
    0xda: ('mul-int/lit8', 2), 0xdb: ('div-int/lit8', 2),
    0xdd: ('and-int/lit8', 2), 0xdc: ('or-int/lit8', 2),
    0x4a: ('aget', 2), 0x44: ('aget-object', 2), 0x4b: ('aput', 2), 0x4c: ('aput-object', 2),
    0x81: ('long-to-int', 1), 0x85: ('int-to-float', 1), 0x86: ('int-to-double', 1),
    0x8a: ('double-to-int', 1), 0x8e: ('double-to-float', 1),
    0x7a00 & 0xff: ('?', 1),
}

def main():
    for cn in CLASSES:
        try:
            with zipfile.ZipFile(APK) as z:
                b = z.read(cn)
        except KeyError:
            continue
        d = Dex(b)
        co = d.find_method(TARGET_CLS, TARGET_METH)
        if co:
            print(f'{cn}: {TARGET_METH} code_off={co:#x}')
            for line in d.disasm(co):
                print(line)
            return
    print('method not found')

main()
