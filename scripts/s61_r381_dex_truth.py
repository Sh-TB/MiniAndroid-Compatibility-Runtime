#!/usr/bin/env python3
"""S61 R-NEW-381 DEX ground truth: Compose class identity under R8.

Questions (from run/s61_r381_repro traces):
  Q1. What are Lt4; / Lho; (the render walk's root + its child)?
  Q2. Does the dooz v23 DEX still contain Landroidx/compose/ classes, or did
      R8 rename the whole library (breaking the engine's prefix gates)?
  Q3. What superclass chain does the AndroidComposeView-side class have, and
      which ancestors override dispatchDraw/onMeasure/onLayout/onDraw?
  Q4. Does Lt4;.onMeasure reach setMeasuredDimension (bridge name present)?
"""
import struct, sys, zipfile
from collections import defaultdict

APK = '/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk'


def uleb(buf, off):
    result = 0; shift = 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return result, off


def load_dex_strings(buf):
    # header: magic(8) checksum(4) sha1(20) file_size(4) header_size(4)
    # endian(4) link_size(4) link_off(4) map_off(4) => string_ids_size@56
    n_strings, off_strings = struct.unpack_from('<2I', buf, 56)
    strings = []
    for i in range(n_strings):
        p = struct.unpack_from('<I', buf, off_strings + i * 4)[0]
        _, p = uleb(buf, p)
        out = bytearray()
        while buf[p] != 0:
            out.append(buf[p]); p += 1
        strings.append(out.decode('utf-8', 'replace'))
    return strings


def parse(buf):
    strings = load_dex_strings(buf)
    n_types, off_types = struct.unpack_from('<2I', buf, 64)
    types = [strings[struct.unpack_from('<I', buf, off_types + i * 4)[0]]
             for i in range(n_types)]
    n_protos = struct.unpack_from('<I', buf, 104)[0]
    off_protos = struct.unpack_from('<I', buf, 108)[0]
    # class_defs
    n_cls, off_cls = struct.unpack_from('<2I', buf, 96)
    classes = {}          # type_desc -> dict
    for i in range(n_cls):
        base = off_cls + i * 32
        c_idx, access, sup_idx, iface_off, src_idx, ann_off, cd_off, sd_off = \
            struct.unpack_from('<8I', buf, base)
        desc = types[c_idx]
        sup = types[sup_idx] if sup_idx != 0xFFFFFFFF else None
        interfaces = []
        if iface_off:
            sz = struct.unpack_from('<I', buf, iface_off)[0]
            for k in range(sz):
                interfaces.append(types[struct.unpack_from('<I', buf, iface_off + 4 + k * 4)[0]])
        classes[desc] = {'access': access, 'super': sup,
                         'interfaces': interfaces, 'cd_off': cd_off}
    return strings, types, classes


def class_data_methods(buf, cd_off):
    """Returns (direct_methods, virtual_methods) as (name_idx, code_off, access)."""
    p = cd_off
    sf, p = uleb(buf, p); inf, p = uleb(buf, p)
    dm, p = uleb(buf, p); vm, p = uleb(buf, p)
    out = {'static_fields': sf, 'instance_fields': inf,
           'direct_methods': [], 'virtual_methods': []}
    idx = 0
    for _ in range(dm):
        d, p = uleb(buf, p); acc, p = uleb(buf, p); coff, p = uleb(buf, p)
        idx += d
        out['direct_methods'].append((idx, acc, coff))
    idx = 0
    for _ in range(vm):
        d, p = uleb(buf, p); acc, p = uleb(buf, p); coff, p = uleb(buf, p)
        idx += d
        out['virtual_methods'].append((idx, acc, coff))
    return out


def main():
    with zipfile.ZipFile(APK) as z:
        dex_names = [n for n in z.namelist() if n.endswith('.dex')]
        print(f"DEX files: {dex_names}")
        alldata = {n: z.read(n) for n in dex_names}

    merged = {}
    for n, buf in alldata.items():
        try:
            strings, types, classes = parse(buf)
            merged[n] = (strings, types, classes)
        except Exception as e:
            print(f"  parse {n}: FAIL {e}")

    # Q2: any Landroidx/compose/ classes at all?
    compose_total = 0
    for n, (strings, types, classes) in merged.items():
        c = sum(1 for t in classes if t.startswith('Landroidx/compose/'))
        print(f"  {n}: androidx/compose classes = {c}")
        compose_total += c
    print(f"Q2 TOTAL androidx/compose classes in DEX: {compose_total}")

    # find candidate classes
    interesting = {}
    for n, (strings, types, classes) in merged.items():
        for t in classes:
            if t in ('Lt4;', 'Lho;') or 'ComposeView' in t or 'AndroidComposeView' in t:
                interesting[t] = (n, classes[t])

    for t, (n, info) in sorted(interesting.items()):
        sup = info['super']
        print(f"\n{t}: super={sup} ifaces={info['interfaces'][:6]}")
        # walk chain
        chain = [t]
        cur = sup
        seen = set()
        while cur and cur not in seen:
            seen.add(cur); chain.append(cur)
            for m, (s2, types2, classes2) in merged.items():
                if cur in classes2:
                    cur = classes2[cur]['super']; break
            else:
                break
        print(f"  chain: {' -> '.join(chain[:12])}")

        # methods of the leaf
        strings = merged[n][0]
        try:
            cd = class_data_methods(alldata[n], info['cd_off'])
            names = []
            for midx, acc, coff in cd['virtual_methods'] + cd['direct_methods']:
                names.append(strings[midx])
            hooks = [m for m in ('onMeasure', 'onLayout', 'onDraw', 'dispatchDraw',
                                 'setMeasuredDimension', 'measure', 'layout')
                     if m in names]
            print(f"  method count={len(names)} lifecycle hooks present: {hooks}")
        except Exception as e:
            print(f"  class_data parse fail: {e}")

    # Q1 summary: what Lho;/Lt4; are
    for t in ('Lho;', 'Lt4;'):
        if t in interesting:
            n, info = interesting[t]
            print(f"\nQ1 {t}: dex={n} super={info['super']}")


if __name__ == '__main__':
    main()
