#!/usr/bin/env python3
"""Minimal direct-DEX dump: fields + toString bytecode of gmdice DiceSet classes.
Independent oracle — does not reuse the runtime's parser (§25 JADX-style check)."""
import struct, zipfile, sys

APK = '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/exp073_real_apps/de.duenndns.gmdice_8.apk'
data = zipfile.ZipFile(APK).read('classes.dex')

def u32(o): return struct.unpack_from('<I', data, o)[0]
def u16(o): return struct.unpack_from('<H', data, o)[0]
def uleb(arr, o):
    r = s = 0
    while True:
        b = arr[o]; o += 1
        r |= (b & 0x7f) << s; s += 7
        if b < 0x80: return r, o

string_ids_off = u32(0x38); string_ids_size = u32(0x40) if False else u32(0x38 - 0) # placeholder
# header layout: string_ids_size @0x38, string_ids_off @0x3c, type_ids @0x44...
string_ids_size = u32(0x38); string_ids_off = u32(0x3c)
type_ids_size = u32(0x40); type_ids_off = u32(0x44)
proto_off = u32(0x4c); field_ids_size = u32(0x50); field_ids_off = u32(0x54)
method_ids_size = u32(0x58); method_ids_off = u32(0x5c)
class_defs_size = u32(0x60); class_defs_off = u32(0x64)

def get_str(idx):
    off = u32(string_ids_off + 4 * idx)
    n, o = uleb(data, off)
    # MUTF-8: quick decode
    end = data.find(b'\x00', o)
    return data[o:end].decode('utf-8', 'replace')

def get_type(idx):
    return get_str(u16(type_ids_off + 4 * idx))

def get_field(idx):
    o = field_ids_off + 8 * idx
    return get_type(u16(o)), get_str(u32(o + 4))

def get_method(idx):
    o = method_ids_off + 8 * idx
    return get_type(u16(o)), get_str(u32(o + 4))

# find classes
for i in range(class_defs_size):
    o = class_defs_off + 32 * i
    type_idx = u32(o)
    cls = get_type(type_idx)
    if cls not in ('Lde/duenndns/gmdice/DiceSet;', 'Lde/duenndns/gmdice/DSADiceSet;'):
        continue
    class_data_off = u32(o + 24)
    print(f'== {cls}')
    sf, off = uleb(data, class_data_off)
    inf, off = uleb(data, off)
    dm, off = uleb(data, off)
    im, off = uleb(data, off)
    fidx = 0
    for _ in range(sf):
        diff, off = uleb(data, off); acc, off = uleb(data, off)
        fidx += diff
        print('   sfield:', get_field(fidx)[1])
    fidx = 0
    for _ in range(inf):
        diff, off = uleb(data, off); acc, off = uleb(data, off)
        fidx += diff
        print('   ifield:', get_field(fidx)[1])
    midx = 0
    for _ in range(dm + im):
        diff, off = uleb(data, off); acc, off = uleb(data, off)
        code_off, off = uleb(data, off)
        midx += diff
        mname = get_method(midx)[1]
        if mname in ('toString', '<init>') and code_off:
            regs = u16(code_off); ins = u16(code_off + 2); insns = u32(code_off + 12)
            bc = data[code_off + 16: code_off + 16 + insns * 2]
            print(f'   method {mname}: regs={regs} ins={ins} units={insns}')
            print('     bytes:', bc.hex(' '))
