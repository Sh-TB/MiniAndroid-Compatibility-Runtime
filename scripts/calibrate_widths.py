#!/usr/bin/env python3
"""Empirically calibrate the dalvik opcode width table.
Walks EVERY method of target classes under candidate tables; a walk is VALID iff
it terminates exactly at the end of the instruction stream without anomalies."""
import struct, zipfile, sys

def uleb128(buf, off):
    r, s = 0, 0
    while True:
        x = buf[off]; off += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, off

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
        sf, p = uleb128(b, p); inf_, p = uleb128(b, p)
        dm, p = uleb128(b, p); vm, p = uleb128(b, p)
        fidx = 0
        for _ in range(sf + inf_):
            d1, p = uleb128(b, p); fidx += d1
            d2, p = uleb128(b, p)
        out = []
        for kind, count in (('direct', dm), ('virtual', vm)):
            midx = 0
            for _ in range(count):
                d1, p = uleb128(b, p); midx += d1
                a, p = uleb128(b, p)
                code_off, p = uleb128(b, p)
                cn, mn = self.method_at(midx)
                out.append((cn, mn, code_off))
        return out
    def code_units(self, code_off):
        b = self.b
        if code_off == 0: return []
        insns_size, = struct.unpack_from('<I', b, code_off + 12)
        insns_off = code_off + 16
        return list(struct.unpack_from('<%dH' % insns_size, b, insns_off))

def build_table(const4_op):
    """const4_op: opcode of const/4 (0x0e old-guess or 0x12 empirical)."""
    W = [1]*256
    base = {  # relative opcodes from const/4
        'const/4': 1, 'const/16': 2, 'const': 3, 'const/high16': 2,
        'const-wide/16': 2, 'const-wide/32': 3, 'const-wide': 5, 'const-wide/high16': 2,
        'const-string': 2, 'const-string/jumbo': 3, 'const-class': 2,
        'monitor-enter': 1, 'monitor-exit': 1, 'check-cast': 2, 'instance-of': 2,
        'array-length': 1, 'new-instance': 2, 'new-array': 2,
        'filled-new-array': 3, 'filled-new-array/range': 3, 'fill-array-data': 3,
        'throw': 1, 'goto': 1, 'goto/16': 2, 'goto/32': 3,
        'packed-switch': 3, 'sparse-switch': 3,
    }
    order = ['const/4','const/16','const','const/high16',
             'const-wide/16','const-wide/32','const-wide','const-wide/high16',
             'const-string','const-string/jumbo','const-class',
             'monitor-enter','monitor-exit','check-cast','instance-of',
             'array-length','new-instance','new-array',
             'filled-new-array','filled-new-array/range','fill-array-data',
             'throw','goto','goto/16','goto/32','packed-switch','sparse-switch']
    for k, w in base.items():
        W[const4_op + order.index(k)] = w
    if_start = const4_op + order.index('sparse-switch') + 1  # cmpl-float
    for o in range(if_start, if_start+5): W[o] = 2          # cmpl-float..cmp-long 23x
    for o in range(if_start+5, if_start+11): W[o] = 2       # if-eq..if-le 22t
    for o in range(if_start+11, if_start+17): W[o] = 2      # if-eqz..if-lez 21t
    for o in range(0x44, 0x52): W[o] = 2   # aget..aput-short
    for o in range(0x52, 0x6e): W[o] = 2   # iget..sput-short 22c/21c
    for o in range(0x6e, 0x73): W[o] = 3   # invokes 35c
    for o in range(0x74, 0x79): W[o] = 3   # invokes/range 3rc
    for o in range(0x7b, 0x90): W[o] = 1   # unary 12x
    for o in range(0x90, 0xb0): W[o] = 2   # binop 23x
    for o in range(0xb0, 0xd0): W[o] = 1   # binop/2addr 12x
    for o in range(0xd0, 0xd8): W[o] = 2   # lit16 22s
    for o in range(0xd8, 0xe3): W[o] = 2   # lit8 22b
    W[0xfa]=4; W[0xfb]=4; W[0xfc]=3; W[0xfd]=3; W[0xfe]=2; W[0xff]=2
    return W

def walk_validate(units, W):
    """Returns True if a linear walk lands EXACTLY on len(units) without anomalies."""
    i, n = 0, len(units)
    steps = 0
    while i < n:
        steps += 1
        if steps > 4000: return False
        op = units[i] & 0xff
        w = W[op]
        if op == 0x00:
            hi = units[i] >> 8
            if hi == 0x01:
                sz = units[i+1] if i+1 < n else 0
                i += 4 + sz; continue
            if hi == 0x02:
                sz = units[i+1] if i+1 < n else 0
                i += 2 + 4*sz; continue
            i += 1; continue
        i += w
    return i == n

def sweep(dexpath, cls):
    z = zipfile.ZipFile(dexpath)
    b = z.read('classes.dex')
    d = Dex(b)
    off = d.find_class(cls)
    methods = d.class_methods(off)
    print(f'{cls}: {len(methods)} methods')
    for c4 in (0x0e, 0x12):
        W = build_table(c4)
        ok = 0
        total = 0
        for cn, mn, code_off in methods:
            if code_off == 0: continue
            units = d.code_units(code_off)
            if not units: continue
            total += 1
            if walk_validate(units, W): ok += 1
        print(f'  const/4 @ 0x{c4:02x}: exact-terminating walks {ok}/{total}')

if __name__ == '__main__':
    sweep('/home/z/my-project/upload/tg/forkgram.apk', 'Lorg/telegram/messenger/MessagesStorage;')
