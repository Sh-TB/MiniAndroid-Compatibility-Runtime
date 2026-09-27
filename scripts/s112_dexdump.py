#!/usr/bin/env python3
"""S112 dexdump-lite: dump method bytecode for target classes/methods.
Parses classes.dex (header, ids, class_defs, code items). Minimal but real."""
import struct, sys

def uleb128(buf, off):
    result, shift = 0, 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80): break
        shift += 7
    return result, off

class Dex:
    def __init__(self, path):
        self.b = open(path, 'rb').read()
        b = self.b
        _, self.str_ids_size, self.str_ids_off, self.type_ids_size, self.type_ids_off, \
            self.proto_ids_size, self.proto_ids_off, self.field_ids_size, self.field_ids_off, \
            self.method_ids_size, self.method_ids_off, self.class_defs_size, self.class_defs_off = \
            struct.unpack_from('<13I', b, 32 + 20)  # after magic/checksum/signature/file_size
        # simpler: header layout
        # string_ids at 0x38, type_ids 0x40, proto 0x48, field 0x50, method 0x58, class 0x60
        (self.str_ids_size, self.str_ids_off) = struct.unpack_from('<II', b, 0x38)
        (self.type_ids_size, self.type_ids_off) = struct.unpack_from('<II', b, 0x40)
        (self.proto_ids_size, self.proto_ids_off) = struct.unpack_from('<II', b, 0x48)
        (self.field_ids_size, self.field_ids_off) = struct.unpack_from('<II', b, 0x50)
        (self.method_ids_size, self.method_ids_off) = struct.unpack_from('<II', b, 0x58)
        (self.class_defs_size, self.class_defs_off) = struct.unpack_from('<II', b, 0x60)
        self.str_cache = {}

    def str_at(self, idx):
        if idx in self.str_cache: return self.str_cache[idx]
        b = self.b
        off = struct.unpack_from('<I', b, self.str_ids_off + idx*4)[0]
        n, off = uleb128(b, off)
        end = off
        while b[end] != 0: end += 1
        s = b[off:end].decode('utf-8', 'replace')
        self.str_cache[idx] = s
        return s

    def type_at(self, idx):
        si = struct.unpack_from('<I', self.b, self.type_ids_off + idx*4)[0]
        return self.str_at(si)

    def method_at(self, idx):
        cls_idx, proto_idx, name_idx = struct.unpack_from('<HHI', self.b, self.method_ids_off + idx*8)
        return self.type_at(cls_idx), self.str_at(name_idx)

    def find_class(self, type_desc):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + i*32
            class_idx, = struct.unpack_from('<I', self.b, off)
            if self.type_at(class_idx) == type_desc:
                return off
        return None

    def class_methods(self, off):
        b = self.b
        class_data_off, = struct.unpack_from('<I', b, off + 24)
        if class_data_off == 0: return []
        p = class_data_off
        static_f, p = uleb128(b, p)
        inst_f, p = uleb128(b, p)
        direct_m, p = uleb128(b, p)
        virtual_m, p = uleb128(b, p)
        out = []
        # static/instance FIELD entries come first (field_idx_diff, access)
        fidx = 0
        for _ in range(static_f + inst_f):
            diff, p = uleb128(b, p)
            fidx += diff
            _acc, p = uleb128(b, p)
        for kind, count in (('direct', direct_m), ('virtual', virtual_m)):
            midx = 0
            for _ in range(count):
                midx_diff, p = uleb128(b, p)
                midx += midx_diff
                access, p = uleb128(b, p)
                code_off, p = uleb128(b, p)
                cn, mn = self.method_at(midx)
                out.append((kind, cn, mn, code_off))
        return out

    def code_units(self, code_off):
        b = self.b
        if code_off == 0: return []
        insns_size, = struct.unpack_from('<I', b, code_off + 12)
        insns_off = code_off + 16
        return list(struct.unpack_from('<%dH' % insns_size, b, insns_off))

    def class_fields(self, off):
        b = self.b
        class_data_off, = struct.unpack_from('<I', b, off + 24)
        access_flags, = struct.unpack_from('<I', b, off + 4)
        superclass_idx, = struct.unpack_from('<I', b, off + 8)
        out = [('access', hex(access_flags), 'super', self.type_at(superclass_idx))]
        if class_data_off == 0: return out
        p = class_data_off
        static_f, p = uleb128(b, p)
        inst_f, p = uleb128(b, p)
        direct_m, p = uleb128(b, p)
        virtual_m, p = uleb128(b, p)
        fidx = 0
        for _ in range(static_f + inst_f):
            diff, p = uleb128(b, p)
            fidx += diff
            acc, p = uleb128(b, p)
            # field_ids: class_idx u2, type_idx u2, name_idx u4
            c_idx, t_idx, n_idx = struct.unpack_from('<HHI', self.b, self.field_ids_off + fidx*8)
            out.append(('field', self.type_at(t_idx), self.str_at(n_idx)))
        return out

if __name__ == '__main__':
    dexpath = sys.argv[1]
    targets = sys.argv[2:]  # e.g. Landroidx/webkit/WebViewFeature; <clinit> isFeatureSupported
    d = Dex(dexpath)
    cls = targets[0]
    want = set(targets[1:])
    off = d.find_class(cls)
    if off is None:
        print('CLASS NOT FOUND in this dex:', cls); sys.exit(0)
    print('class', cls, 'class_def_off', hex(off))
    for kind, cn, mn, code_off in d.class_methods(off):
        if want and mn not in want: continue
        units = d.code_units(code_off)
        print(f'\n--- {kind} {cn}.{mn} code_off={hex(code_off)} units={len(units)}')
        print(' '.join('%04x' % u for u in units[:400]))
