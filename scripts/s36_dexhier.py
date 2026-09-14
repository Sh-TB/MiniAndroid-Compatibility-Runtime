#!/usr/bin/env python3
"""S36: raw DEX class_def parse — resolve z1/i superclass chain without androguard."""
import struct, sys, zipfile

APK = '/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk'

data = zipfile.ZipFile(APK).read('classes.dex')


def u4(o): return struct.unpack_from('<I', data, o)[0]
def u2(o): return struct.unpack_from('<H', data, o)[0]
def u1(o): return data[o]


string_ids_size, string_ids_off = u4(0x38), u4(0x3c)
type_ids_size, type_ids_off = u4(0x40), u4(0x44)
field_off = 0x48
proto_off = 0x4c
class_defs_size, class_defs_off = u4(0x60), u4(0x64)


def get_string(idx):
    off = u4(string_ids_off + idx * 4)
    # uleb128 length
    b0 = u1(off); off += 1
    if b0 >= 0x80:
        b1 = u1(off); off += 1
        n = (b0 & 0x7f) | (b1 << 7)
    else:
        n = b0
    out = []
    for _ in range(n):
        c = u1(off); off += 1
        if c == 0:
            break
        out.append(chr(c))
    return ''.join(out)


def get_type(idx):
    return get_string(u4(type_ids_off + idx * 4))


classes = {}
for i in range(class_defs_size):
    off = class_defs_off + i * 32
    class_idx = u4(off)
    superclass_idx = u4(off + 8)
    classes[get_type(class_idx)] = get_type(superclass_idx) if superclass_idx != 0xFFFFFFFF else None


target = sys.argv[1] if len(sys.argv) > 1 else 'Lz1/i;'
chain = []
cur = target
while cur and cur in classes:
    chain.append(f'{cur} extends {classes[cur]}')
    cur = classes[cur]
for link in chain:
    print(link)
