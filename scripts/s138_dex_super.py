#!/usr/bin/env python3
"""s138_dex_super.py — read class_defs/superclass edges from the dooz DEX
for the modifier-family R8 classes (TRAIN-31 follow-up probe)."""
import struct, sys, zipfile

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
WANT = {'Lmo;', 'Ltl0;', 'Lga;', 'Lok0;', 'Lfa;', 'Lff;', 'Lu20;', 'Lzy0;',
        'Lqp;', 'Lm4;', 'Lx10;', 'Lto0;', 'Lhv;'}

def read_uleb(buf, off):
    result = 0; shift = 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80): break
        shift += 7
    return result, off

z = zipfile.ZipFile(APK)
dex_names = [n for n in z.namelist() if n.endswith('.dex')]
print('dex files:', dex_names)
for name in dex_names:
    d = z.read(name)
    if d[:4] != b'dex\n': continue
    string_ids_size, string_ids_off = struct.unpack_from('<II', d, 0x38)
    type_ids_size, type_ids_off = struct.unpack_from('<II', d, 0x40)
    class_defs_size, class_defs_off = struct.unpack_from('<II', d, 0x60)
    # strings
    def get_str(idx):
        off = struct.unpack_from('<I', d, string_ids_off + 4 * idx)[0]
        n, off = read_uleb(d, off)
        end = d.index(b'\x00', off)
        return d[off:end].decode('utf-8', 'replace')
    def get_type(idx):
        si = struct.unpack_from('<I', d, type_ids_off + 4 * idx)[0]
        return get_str(si)
    hits = {}
    for i in range(class_defs_size):
        off = class_defs_off + 32 * i
        class_idx, access, super_idx = struct.unpack_from('<III', d, off)
        cls = get_type(class_idx)
        if cls in WANT:
            sup = get_type(super_idx) if super_idx != 0xFFFFFFFF else '<none>'
            hits[cls] = sup
    if hits:
        print(f'-- {name} ({class_defs_size} classes) --')
        for k in sorted(hits):
            print(f'   {k}  extends  {hits[k]}')
        missing = WANT - set(hits)
        if missing:
            print('   not defined here:', sorted(missing))
