#!/usr/bin/env python3
"""Dump CellListener.onClick from the tictactoe_golden fixture DEX.
Independent oracle — does not reuse the runtime parser (§25 JADX-style check)."""
import struct, zipfile, sys

APK = sys.argv[1] if len(sys.argv) > 1 else '/tmp/ttt_golden.apk'
TARGET = sys.argv[2] if len(sys.argv) > 2 else 'CellListener'
METHOD = sys.argv[3] if len(sys.argv) > 3 else 'onClick'
data = zipfile.ZipFile(APK).read('classes.dex')

def u32(o): return struct.unpack_from('<I', data, o)[0]
def u16(o): return struct.unpack_from('<H', data, o)[0]
def uleb(arr, o):
    r = s = 0
    while True:
        b = arr[o]; o += 1
        r |= (b & 0x7f) << s; s += 7
        if b < 0x80: return r, o

string_ids_size = u32(0x38); string_ids_off = u32(0x3c)
type_ids_size = u32(0x40); type_ids_off = u32(0x44)
proto_ids_off = u32(0x4c)
field_ids_size = u32(0x50); field_ids_off = u32(0x54)
method_ids_size = u32(0x58); method_ids_off = u32(0x5c)
class_defs_size = u32(0x60); class_defs_off = u32(0x64)

def get_str(idx):
    off = u32(string_ids_off + 4 * idx)
    n, o = uleb(data, off)
    end = data.find(b'\x00', o)
    return data[o:end].decode('utf-8', 'replace')

def get_type(idx):
    return get_str(u16(type_ids_off + 4 * idx))

def get_field(idx):
    o = field_ids_off + 8 * idx
    return get_type(u16(o)), get_str(u32(o + 4)), get_type(u16(o + 2))

def get_proto(idx):
    o = proto_ids_off + 12 * idx
    ret = get_type(u16(o + 4))
    po = u32(o + 8)
    params = []
    if po:
        sz = u32(po)
        params = [get_type(u16(po + 4 + 2 * j)) for j in range(sz)]
    return '(' + ' '.join(params) + ')' + ret

def get_method(idx):
    o = method_ids_off + 8 * idx
    return get_type(u16(o)), get_str(u32(o + 4)), get_proto(u16(o + 2))

INVOKE = {0x6e: 'invoke-virtual', 0x6f: 'invoke-super', 0x70: 'invoke-direct',
          0x71: 'invoke-static', 0x72: 'invoke-interface'}

def print_method(m, code_off):
    print(f'== {m[0]} {m[1]} {m[2]}')
    if not code_off:
        return
    insns_off = code_off + 16
    insns_sz = u32(code_off + 12)
    k = 0
    while k < insns_sz:
        w = u16(insns_off + 2 * k)
        op = w & 0xff
        units = 1
        line = f'  {k:3d}: op={op:#04x} {w:#06x}'
        if op in INVOKE:
            mi = u16(insns_off + 2 * (k + 1))
            mm = get_method(mi)
            line += f' {INVOKE[op]} {mm[0].split("/")[-1]}.{mm[1]}{mm[2]}'
            units = 3
        elif op == 0x74:
            mi = u16(insns_off + 2 * (k + 2))
            mm = get_method(mi)
            line += f' invoke-range {mm[0].split("/")[-1]}.{mm[1]}{mm[2]}'
            units = 3
        elif op == 0x22:
            line += f' new-instance {get_type(u16(insns_off + 2 * (k + 1)))}'
            units = 2
        elif op == 0x1a:
            line += f' const-string "{get_str(u16(insns_off + 2 * (k + 1)))}"'
            units = 2
        elif op == 0x1b:
            si = struct.unpack_from('<I', data, insns_off + 2 * (k + 1))[0]
            line += f' const-string/jumbo "{get_str(si)}"'
            units = 3
        elif 0x52 <= op <= 0x61:
            f, fn, ft = get_field(u16(insns_off + 2 * (k + 1)))
            line += f' {f.split("/")[-1]}.{fn}:{ft}'
            units = 2
        print(line)
        k += units

for i in range(class_defs_size):
    o = class_defs_off + 32 * i
    cls = get_type(u32(o))
    if TARGET not in cls:
        continue
    class_data_off = u32(o + 24)
    sf, off = uleb(data, class_data_off)
    inf, off = uleb(data, off)
    dm, off = uleb(data, off)
    im, off = uleb(data, off)
    fidx = 0
    for _ in range(sf):
        d, off = uleb(data, off); acc, off = uleb(data, off); fidx += d
    for _ in range(inf):
        d, off = uleb(data, off); acc, off = uleb(data, off); fidx += d
    for _ in range(dm):
        d, off = uleb(data, off); acc, off = uleb(data, off)
        co, off = uleb(data, off); fidx += d
        m = get_method(fidx)
        if m[1] != METHOD:
            continue
        print_method(m, co)
    for _ in range(im):
        d, off = uleb(data, off); acc, off = uleb(data, off)
        co, off = uleb(data, off); fidx += d
        m = get_method(fidx)
        if m[1] != METHOD:
            continue
        print_method(m, co)
