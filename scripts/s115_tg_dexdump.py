#!/usr/bin/env python3
"""S115 Telegram frontier — DEX ground truth: string constants + invoke targets of
MessagesStorage.lambda$loadDialogFilters$67. Uses the proven s112 Dex parser (code_off is ULEB)."""
import struct, sys, zipfile
sys.path.insert(0, '/home/z/my-project/scripts')

APK = '/home/z/my-project/upload/tg/forkgram.apk'

def uleb128(buf, off):
    result, shift = 0, 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80): break
        shift += 7
    return result, off

class Dex:
    def __init__(self, b):
        self.b = b
        (self.str_ids_size, self.str_ids_off) = struct.unpack_from('<II', b, 0x38)
        (self.type_ids_size, self.type_ids_off) = struct.unpack_from('<II', b, 0x40)
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
        fidx = 0
        for _ in range(static_f + inst_f):
            diff, p = uleb128(b, p); fidx += diff
            _acc, p = uleb128(b, p)
        for kind, count in (('direct', direct_m), ('virtual', virtual_m)):
            midx = 0
            for _ in range(count):
                midx_diff, p = uleb128(b, p); midx += midx_diff
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

def walk_strings(d, units):
    """Walk insns; emit const-string entries + invoke targets + approx pc for each."""
    out = []
    i = 0
    n = len(units)
    while i < n:
        op = units[i]
        if op == 0x1a:
            sidx = units[i+1]
            out.append((i, 'const-string', d.str_at(sidx) if sidx < d.str_ids_size else '?'))
            i += 2
        elif op == 0x1b:
            sidx = units[i+1] | (units[i+2] << 16)
            out.append((i, 'const-string/jumbo', d.str_at(sidx) if sidx < d.str_ids_size else '?'))
            i += 3
        elif 0x6e <= op <= 0x72:
            m_idx = units[i+1]
            cn, mn = d.method_at(m_idx) if m_idx < d.method_ids_size else ('?', '?')
            out.append((i, 'invoke', f'{cn}->{mn}'))
            i += 3
        elif 0x74 <= op <= 0x78:
            m_idx = units[i+1]
            cn, mn = d.method_at(m_idx) if m_idx < d.method_ids_size else ('?', '?')
            out.append((i, 'invoke-range', f'{cn}->{mn}'))
            i += 3
        elif op == 0x0100 or op == 0x0200:
            sz = units[i+1]
            i += 2 + (sz*(2 if op == 0x0100 else 4) + 1)//2
        else:
            i += 1
    return out

z = zipfile.ZipFile(APK)
CLS = 'Lorg/telegram/messenger/MessagesStorage;'
NAME_SUB = 'loadDialogFilters'
for dexname in ['classes.dex', 'classes2.dex', 'classes3.dex', 'classes4.dex', 'classes5.dex']:
    b = z.read(dexname)
    if b'loadDialogFilters' not in b:
        continue
    d = Dex(b)
    off = d.find_class(CLS)
    if off is None:
        print(dexname, 'class not found'); continue
    print(f'== {dexname} {CLS}')
    for kind, cn, mn, code_off in d.class_methods(off):
        if NAME_SUB not in mn: continue
        units = d.code_units(code_off)
        print(f'--- {kind} {cn}.{mn} code_off={hex(code_off)} units={len(units)}')
        for pc, tag, val in walk_strings(d, units):
            print(f'  +{pc:05d} {tag}: {val[:160]}')
    break
