#!/usr/bin/env python3
"""F-NEW-197 evidence: disassemble SlidingUpPanelLayout.<init> + setGravity
from opencalculator_53.apk to prove the gravity defValue register truth."""
import struct, sys, zipfile

APK = '/home/z/my-project/upload/opencalculator_53.apk'
TARGET = 'Lcom/sothree/slidinguppanel/SlidingUpPanelLayout;'

def uleb(buf, off):
    result = 0; shift = 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return result, off

def read_header(d):
    string_ids_size, string_ids_off = struct.unpack_from('<II', d, 0x38)
    type_ids_size, type_ids_off = struct.unpack_from('<II', d, 0x40)
    proto_ids_size, proto_ids_off = struct.unpack_from('<II', d, 0x48)
    field_ids_size, field_ids_off = struct.unpack_from('<II', d, 0x50)
    method_ids_size, method_ids_off = struct.unpack_from('<II', d, 0x58)
    class_defs_size, class_defs_off = struct.unpack_from('<II', d, 0x60)
    return dict(string_ids=(string_ids_size, string_ids_off),
                type_ids=(type_ids_size, type_ids_off),
                method_ids=(method_ids_size, method_ids_off),
                class_defs=(class_defs_size, class_defs_off),
                field_ids=(field_ids_size, field_ids_off))

class Dex:
    def __init__(self, d):
        self.d = d
        self.h = read_header(d)
        # string table
        sz, off = self.h['string_ids']
        self.strs = []
        for i in range(sz):
            so = struct.unpack_from('<I', d, off + i*4)[0]
            slen, doff = uleb(d, so)
            raw = d[doff:doff+slen*4]
            s = raw.decode('utf-8', errors='replace').split('\x00')[0]
            self.strs.append(s)
        # type ids
        sz, off = self.h['type_ids']
        self.types = []
        for i in range(sz):
            si = struct.unpack_from('<I', d, off + i*4)[0]
            self.types.append(self.strs[si])
        # method ids
        sz, off = self.h['method_ids']
        self.methods = []
        for i in range(sz):
            cls, proto, name = struct.unpack_from('<HHI', d, off + i*8)
            self.methods.append((self.types[cls], self.strs[name]))
        # field ids
        sz, off = self.h['field_ids']
        self.fields = []
        for i in range(sz):
            cls, typ, name = struct.unpack_from('<HHI', d, off + i*8)
            self.fields.append((self.types[cls], self.types[typ], self.strs[name]))

    def find_class(self, desc):
        d = self.d
        sz, off = self.h['class_defs']
        for i in range(sz):
            cd = off + i*32
            cls_idx, _access, super_idx, _i1, _i2, _s1, class_data_off, _sv = struct.unpack_from('<IIIIIIII', d, cd)
            if self.types[cls_idx] == desc:
                return class_data_off
        return None

    def methods_of(self, class_data_off):
        d = self.d
        off = class_data_off
        static_f, off = uleb(d, off)
        inst_f, off = uleb(d, off)
        direct_m, off = uleb(d, off)
        virtual_m, off = uleb(d, off)
        for _ in range(static_f + inst_f):
            _, off = uleb(d, off)  # field idx diff
            _, off = uleb(d, off)  # access
        out = []
        midx = 0
        for _ in range(direct_m + virtual_m):
            midx_delta, off = uleb(d, off)
            midx += midx_delta
            access, off = uleb(d, off)
            code_off, off = uleb(d, off)
            out.append((midx, access, code_off))
        return out

INS_FMT = {}

def disassemble(code, registers, dex):
    """Minimal walk printing invoke/getInt-adjacent instructions with pcs."""
    insns_size, = struct.unpack_from('<I', code, 0x0c)
    insns_off = 0x10
    pc = 0
    out = []
    while pc < insns_size:
        w = struct.unpack_from('<H', code, insns_off + pc*2)[0]
        op = w & 0xff
        # invoke-kind: op 0x6e..0x72 → format35c
        if 0x6e <= op <= 0x72:
            midx = struct.unpack_from('<H', code, insns_off + pc*2 + 2)[0]
            cls, name = dex.methods[midx][0], dex.methods[midx][1]
            out.append((pc, f'invoke-kind[{op:#x}] {cls}.{name}'))
            pc += 3
        elif op == 0x12:  # const/4
            out.append((pc, f'const/4 {((w>>8)&0xf)} {((w>>12)&0xf)-16 if (w>>12)&0x8 else (w>>12)&0xf}'))
            pc += 1
        elif op == 0x13:  # const/16
            v = struct.unpack_from('<h', code, insns_off + pc*2 + 2)[0]
            out.append((pc, f'const/16 v{(w>>8)&0xff} {v}'))
            pc += 2
        elif op == 0x1a:  # const-string
            si = struct.unpack_from('<H', code, insns_off + pc*2 + 2)[0]
            out.append((pc, f'const-string "{dex.strs[si][:40]}"'))
            pc += 2
        elif 0x52 <= op <= 0x5f:  # iget/iput family (format22c)
            fidx = struct.unpack_from('<H', code, insns_off + pc*2 + 2)[0]
            f = dex.fields[fidx]
            out.append((pc, f'op[{op:#x}] field {f[0]}.{f[2]}:{f[1]}'))
            pc += 2
        elif op in (0x74, 0x77):  # invoke-custom / interface range? just skip
            pc += 3
        else:
            pc += 1
        if len(out) > 4000: break
    return out

def main():
    z = zipfile.ZipFile(APK)
    dex_files = [n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]
    for name in dex_files:
        d = z.read(name)
        dex = Dex(d)
        cdo = dex.find_class(TARGET)
        if cdo is None:
            continue
        print(f'=== {name}: {TARGET} ===')
        for midx, access, code_off in dex.methods_of(cdo):
            cls, mname = dex.methods[midx]
            if mname not in ('<init>', 'setGravity'):
                continue
            print(f'--- method {mname} (code_off={code_off:#x}) ---')
            if code_off == 0:
                print('  (abstract/native)')
                continue
            registers, ins_in, ins_out = struct.unpack_from('<HHH', d, code_off + 4)
            insns_size, = struct.unpack_from('<I', d, code_off + 0x0c)
            print(f'  registers={registers} ins={ins_in} outs={ins_out} insns={insns_size}')
            # walk invokes with ABSOLUTE pc printed
            code = d[code_off:code_off + 0x10 + insns_size*2]
            for pc, line in disassemble(code, registers, dex):
                print(f'  pc={pc:#06x} {line}')

if __name__ == '__main__':
    main()
