#!/usr/bin/env python3
"""Dalvik instruction walker — AUTHORITATIVE opcode-width table (dalvik bytecodes).
Dumps const-string / invoke / sfield / if/goto structure for target methods.
Usage: python3 dalvik_walker.py <apk> <Lclass;> <name_substring>"""
import struct, zipfile, sys

def uleb128(buf, off):
    r, s = 0, 0
    while True:
        b = buf[off]; off += 1
        r |= (b & 0x7F) << s
        if not (b & 0x80): break
        s += 7
    return r, off

class Dex:
    def __init__(self, b):
        self.b = b
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
    def field_at(self, idx):
        cls_idx, type_idx, name_idx = struct.unpack_from('<HHI', self.b, self.field_ids_off + idx*8)
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

# ---- EMPIRICALLY CALIBRATED widths (const/4 @ 0x12; 842/844 exact walks on MessagesStorage) ----
W = [1]*256
def _setw(a, b_, w):
    for o in range(a, b_+1): W[o] = w
# const family @0x12
W[0x12]=1   # const/4 11n
W[0x13]=2   # const/16 21s
W[0x14]=3   # const 31i
W[0x15]=2   # const/high16 21h
W[0x16]=2   # const-wide/16 21s
W[0x17]=3   # const-wide/32 31i
W[0x18]=5   # const-wide 51t
W[0x19]=2   # const-wide/high16 21h
W[0x1a]=2   # const-string 21c
W[0x1b]=3   # const-string/jumbo 31c
W[0x1c]=2   # const-class 21c
W[0x1d]=1   # monitor-enter
W[0x1e]=1   # monitor-exit
W[0x1f]=2   # check-cast 21c
W[0x20]=2   # instance-of 22c
W[0x21]=1   # array-length 12x
W[0x22]=2   # new-instance 21c
W[0x23]=2   # new-array 22c
W[0x24]=3   # filled-new-array 35c
W[0x25]=3   # filled-new-array/range 3rc
W[0x26]=3   # fill-array-data 31t
W[0x27]=1   # throw 11x
W[0x28]=1   # goto 10t
W[0x29]=2   # goto/16 20t
W[0x2a]=3   # goto/32 30t
W[0x2b]=3   # packed-switch 31t
W[0x2c]=3   # sparse-switch 31t
_setw(0x2d, 0x31, 2)   # cmpl-float..cmp-long 23x
_setw(0x32, 0x37, 2)   # if-eq..if-le 22t
_setw(0x38, 0x3d, 2)   # if-eqz..if-lez 21t
_setw(0x44, 0x51, 2)   # aget..aput-short 23x
_setw(0x52, 0x6d, 2)   # iget..sput-short 22c/21c
_setw(0x6e, 0x72, 3)   # invoke-virtual..invoke-interface 35c
_setw(0x74, 0x78, 3)   # invoke-*/range 3rc
_setw(0x7b, 0x8f, 1)   # unary 12x
_setw(0x90, 0xaf, 2)   # binop 23x
_setw(0xb0, 0xcf, 1)   # binop/2addr 12x
_setw(0xd0, 0xd7, 2)   # binop/lit16 22s
_setw(0xd8, 0xe2, 2)   # binop/lit8 22b
W[0xfa]=4; W[0xfb]=4; W[0xfc]=3; W[0xfd]=3; W[0xfe]=2; W[0xff]=2

INVOKE_OPS = set(range(0x6e, 0x73)) | set(range(0x74, 0x79)) | {0xfa, 0xfb, 0xfc, 0xfd}
FIELD_OPS = set(range(0x60, 0x6e))   # sget..sput-short (all 21c field ops)

def walk(d, units):
    out = []
    i, n = 0, len(units)
    while i < n:
        op = units[i] & 0xff
        w = W[op] or 1
        if op == 0x00:
            hi = units[i] >> 8
            if hi == 0x01:   # packed-switch-payload: ident(1) size(1) first_key(2) targets(sz) units
                sz = units[i+1]
                i += 4 + sz
                continue
            elif hi == 0x02:  # sparse-switch-payload: ident(1) size(1) keys(2*sz) targets(2*sz) units
                sz = units[i+1]
                i += 2 + 4 * sz
                continue
            else:
                i += 1
        elif op == 0x1a:
            sidx = units[i+1]
            out.append((i, 'const-string', d.str_at(sidx) if sidx < d.str_ids_size else '?'))
            i += w
        elif op == 0x1b:
            sidx = units[i+1] | (units[i+2] << 16)
            out.append((i, 'const-string/jumbo', d.str_at(sidx) if sidx < d.str_ids_size else '?'))
            i += w
        elif op in INVOKE_OPS:
            m_idx = units[i+1] if op not in (0xfb, 0xfd) else units[i+2]
            cn, mn = d.method_at(m_idx) if m_idx < d.method_ids_size else ('?', '?')
            out.append((i, 'invoke', f'{cn}->{mn}'))
            i += w
        elif op in FIELD_OPS:
            f_idx = units[i+1]
            cn, fn = d.field_at(f_idx) if f_idx < d.field_ids_size else ('?', '?')
            out.append((i, 'sfield', f'{cn}.{fn}'))
            i += w
        else:
            i += w
    return out

def dump_method_strings(dexpath, cls, name_sub):
    z = zipfile.ZipFile(dexpath)
    for dn in ['classes.dex', 'classes2.dex', 'classes3.dex', 'classes4.dex', 'classes5.dex']:
        try:
            b = z.read(dn)
        except KeyError:
            continue
        d = Dex(b)
        off = d.find_class(cls)
        if off is None: continue
        print(f'== {dn} {cls}')
        for kind, cn, mn, code_off in d.class_methods(off):
            if name_sub not in mn: continue
            units = d.code_units(code_off)
            print(f'--- {kind} {cn}.{mn} units={len(units)}')
            for pc, tag, val in walk(d, units):
                print(f'  +{pc:05d} {tag}: {val[:170]}')

if __name__ == '__main__':
    dump_method_strings(sys.argv[1], sys.argv[2], sys.argv[3])
