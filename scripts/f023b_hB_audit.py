#!/usr/bin/env python3
"""F-023b: enumerate every method of a class in the dooz DEX with protos +
class fields, then disassemble selected methods. Uses exp059_disasm tables."""
import zipfile, sys, struct
sys.path.insert(0, '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/tools')
import exp059_disasm as d

APK = '/home/z/my-project/apk_cache/corpus/dooz.apk'

def uleb(data, off):
    result = 0; shift = 0
    while True:
        b = data[off]; off += 1
        result |= (b & 0x7f) << shift
        shift += 7
        if not (b & 0x80): break
    return result, off

def sleb(data, off):
    result = 0; shift = 0
    while True:
        b = data[off]; off += 1
        result |= (b & 0x7f) << shift
        shift += 7
        if not (b & 0x80):
            if b & 0x40:
                result -= (1 << shift)
            break
    return result, off

def main():
    target = sys.argv[1]  # e.g. "Lh/B;"
    with zipfile.ZipFile(APK) as z:
        data = z.read('classes.dex')
    dex = d.load_dex(data)
    raw = dex['data']

    # class def lookup
    for i in range(dex['class_defs_size']):
        off = dex['class_defs_off'] + i * 32
        cls_idx, access, sup, iface_off, src, ann, cd_off, svals = struct.unpack_from('<8I', raw, off)
        cls = d.get_type(dex, cls_idx)
        if cls != target: continue
        print(f'=== class {cls} access=0x{access:x} super={d.get_type(dex,sup) if sup else "-"} ===')
        # class_data
        if cd_off == 0:
            print('  (no class_data)'); return
        o = cd_off
        sf, inf, dm, vm = (uleb(raw, o + k) for k in range(4))
        # need sequential parse:
        o = cd_off
        sf, o = uleb(raw, o); inf, o = uleb(raw, o)
        dm, o = uleb(raw, o); vm, o = uleb(raw, o)
        fidx = 0
        print(f'--- static fields ({sf}) ---')
        for _ in range(sf):
            diff, o = uleb(raw, o); fidx += diff; acc, o = uleb(raw, o)
            fid = dex['field_ids_off'] + fidx * 8
            ci, ti, ni = struct.unpack_from('<HHI', raw, fid)
            print(f'  {d.get_type(dex,ti)} {d.get_string(dex,ni)} (0x{acc:x})')
        fidx = 0
        if inf:
            print(f'--- instance fields ({inf}) ---')
        for _ in range(inf):
            diff, o = uleb(raw, o); fidx += diff; acc, o = uleb(raw, o)
            fid = dex['field_ids_off'] + fidx * 8
            ci, ti, ni = struct.unpack_from('<HHI', raw, fid)
            print(f'  {d.get_type(dex,ti)} {d.get_string(dex,ni)} (0x{acc:x})')
        midx = 0
        print(f'--- direct methods ({dm}) ---')
        for _ in range(dm):
            diff, o = uleb(raw, o); midx += diff; acc, o = uleb(raw, o)
            code_off, o = uleb(raw, o)
            mid = dex['method_ids_off'] + midx * 8
            ci, pi, ni = struct.unpack_from('<HHI', raw, mid)
            print(f'  {d.get_string(dex,ni)} {d.get_proto(dex,pi)} code=0x{code_off:x}')
        midx = 0
        print(f'--- virtual methods ({vm}) ---')
        for _ in range(vm):
            diff, o = uleb(raw, o); midx += diff; acc, o = uleb(raw, o)
            code_off, o = uleb(raw, o)
            mid = dex['method_ids_off'] + midx * 8
            ci, pi, ni = struct.unpack_from('<HHI', raw, mid)
            print(f'  {d.get_string(dex,ni)} {d.get_proto(dex,pi)} code=0x{code_off:x}')

if __name__ == '__main__':
    main()
