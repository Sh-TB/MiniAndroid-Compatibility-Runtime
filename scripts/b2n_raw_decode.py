#!/usr/bin/env python3
"""Raw code-unit decode of one method: verify const-string operands."""
import struct, sys, zipfile

path, cls, method = sys.argv[1], sys.argv[2], sys.argv[3]

with zipfile.ZipFile(path) as z:
    dex = z.read('classes.dex')

def u32(o): return struct.unpack_from('<I', dex, o)[0]
def u16(o): return struct.unpack_from('<H', dex, o)[0]
def uleb(o):
    r = 0; s = 0
    while True:
        b = dex[o]; o += 1
        r |= (b & 0x7f) << s; s += 7
        if not (b & 0x80): break
    return r, o

def string_at(idx):
    off = u32(0x3C + 4 * idx)
    p = off; r = 0; s = 0
    while True:
        b = dex[p]; p += 1
        r |= (b & 0x7f) << s; s += 7
        if not (b & 0x80): break
    end = dex.find(b'\x00', p)
    return dex[p:end].decode('utf-8', 'replace')

# type_ids / proto_ids / field_ids / method_ids
string_ids_size = u32(0x38)
type_ids_off = u32(0x44)
field_ids_off = u32(0x54)
method_ids_off = u32(0x5C)
def type_str(tidx):
    sidx = u32(type_ids_off + 4 * tidx)
    return string_at(sidx)
def field_str(fidx):
    o = field_ids_off + 8 * fidx
    cls_t, typ_t, name_s = u16(o), u16(o+2), u32(o+4)
    return f"{type_str(cls_t)}.{string_at(name_s)}:{type_str(typ_t)}"
def method_str(midx):
    o = method_ids_off + 8 * midx
    cls_t, _, name_s = u16(o), u16(o+2), u32(o+4)
    return f"{type_str(cls_t)}.{string_at(name_s)}"

# class_defs walk: method_id deltas accumulate ACROSS classes (file order)
class_defs_off = u32(0x64); class_defs_size = u32(0x60)
midx = 0; fidx = 0
found = False
for i in range(class_defs_size):
    o = class_defs_off + 32 * i
    tidx = u32(o)
    cf_off = u32(o + 24)  # class_data_off
    if cf_off == 0:
        continue
    p = cf_off
    sf_n, p = uleb(p); inf_n, p = uleb(p)
    dm_n, p = uleb(p); vm_n, p = uleb(p)
    midx = 0; fidx = 0  # per-class reset (dex spec: diff within class_data stream)
    for _ in range(sf_n):
        d, p = uleb(p); fidx += d; _, p = uleb(p)
    for _ in range(inf_n):
        d, p = uleb(p); fidx += d; _, p = uleb(p)
    for _ in range(dm_n):
        d, p = uleb(p); midx += d; acc, p = uleb(p); co, p = uleb(p)
        if midx > 100000:
            print(f"!! midx divergence at class {type_str(tidx)} i={i} dm; midx={midx}")
            sys.exit(1)
        if not found and type_str(tidx) == cls \
           and string_at(u32(method_ids_off + 8 * midx + 4)) == method:
            insns_off = u32(co + 12); insns_size = u32(co + 16)
            print(f"{cls}.{method} code_off={hex(co)} insns_off={hex(insns_off)} size={insns_size}")
            for k in range(insns_size):
                unit = u16(insns_off * 2 + 2 * k)
                op = unit & 0xff
                line = f"  [{k:3}] {unit:#06x} op={op:#04x}"
                if op == 0x1a:  # const-string
                    sidx = (unit >> 16) & 0xffff
                    line += f" const-string v{(unit>>8)&0xff} idx={sidx} -> {string_at(sidx)!r}"
                elif op in (0x6e, 0x71):  # invoke-virtual / invoke-static (low 16 bits)
                    mid = (unit >> 16) & 0xffff
                    line += f" invoke(low16={mid}) {method_str(mid)}"
                elif op == 0x22:  # new-instance
                    t = (unit >> 16) & 0xffff
                    line += f" new-instance v{(unit>>8)&0xff} {type_str(t)}"
                elif op == 0x1c:  # const-class
                    t = (unit >> 16) & 0xffff
                    line += f" const-class v{(unit>>8)&0xff} {type_str(t)}"
                elif op == 0x67:  # sput-object
                    line += f" sput-object field={field_str((unit >> 16) & 0xffff)}"
                print(line)
            found = True
        if found:
            break
    if found:
        break
