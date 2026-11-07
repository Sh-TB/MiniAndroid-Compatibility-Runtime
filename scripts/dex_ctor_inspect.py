#!/usr/bin/env python3
"""Inspect constructors of a DEX class (F274-CTORGATE verification)."""
import struct, zipfile, sys

apk = sys.argv[1]
target = sys.argv[2]  # e.g. 'Ls1/l1;'
z = zipfile.ZipFile(apk)
for dexname in [n for n in z.namelist() if n.endswith('.dex')]:
    data = z.read(dexname)
    u4 = lambda o: struct.unpack_from('<I', data, o)[0]
    u2 = lambda o: struct.unpack_from('<H', data, o)[0]
    string_ids_off = u4(0x3c); type_ids_off = u4(0x44)
    proto_ids_off = u4(0x4c); method_ids_off = u4(0x5c)
    class_defs_size = u4(0x60); class_defs_off = u4(0x64)

    def get_string(idx):
        off = u4(string_ids_off + 4 * idx)
        result = 0; shift = 0; p = off
        while True:
            b = data[p]; p += 1
            result |= (b & 0x7f) << shift; shift += 7
            if not (b & 0x80): break
        return data[p:p + result].decode('utf-8', 'ignore')

    def get_type(idx): return get_string(u4(type_ids_off + 4 * idx))

    def get_proto(idx):
        po = proto_ids_off + 12 * idx
        ret = get_type(u4(po + 4))
        params_off = u4(po + 8)
        params = []
        if params_off:
            n = u4(params_off)
            for i in range(n):
                params.append(get_type(u4(params_off + 4 * i)))
        return '(' + ', '.join(params) + ')' + ret

    for ci in range(class_defs_size):
        co = class_defs_off + 32 * ci
        if get_type(u4(co)) != target: continue
        print(f'{dexname}: {target} super={get_type(u4(co+8))}')
        class_data_off = u4(co + 24)
        if not class_data_off:
            print('  NO class_data'); sys.exit(0)
        p = [class_data_off]
        def uleb():
            r = 0; s = 0
            while True:
                b = data[p[0]]; p[0] += 1
                r |= (b & 0x7f) << s; s += 7
                if not (b & 0x80): break
            return r
        for _ in range(uleb()): uleb(); uleb()   # static fields
        for _ in range(uleb()): uleb(); uleb()   # instance fields
        midx = 0
        n_dm = uleb()
        for _ in range(n_dm):
            midx += uleb(); uleb(); code_off = uleb()
            mid = method_ids_off + 8 * midx
            mname = get_string(u2(mid))
            if mname == '<init>':
                print('  DIRECT <init>', get_proto(u2(mid + 4)), 'code_off=', code_off)
        n_vm = uleb()
        for _ in range(n_vm):  # diff counter CONTINUES from direct methods
            midx += uleb(); uleb(); code_off = uleb()
            mid = method_ids_off + 8 * midx
            mname = get_string(u2(mid))
            if mname == '<init>':
                print('  VIRT <init>', get_proto(u2(mid + 4)))
        sys.exit(0)
print(target, 'NOT FOUND in any dex')
