#!/usr/bin/env python3
"""cont18i_fieldkey_audit.py — F-NEW-271 static arm: field-key type-collision audit.

Laws under test:
  ART field identity = (declaring class, name, TYPE). The engine's s134 key
  is class + "->" + name — TYPE IS NOT PART OF THE KEY. If any DEX class
  declares two instance fields with the SAME name and DIFFERENT types, both
  collapse into one engine slot (last writer wins) — exactly the alien-typed
  slot face F-271 recorded (Lnb0.j holding STRING_REF where :Lqb0 expected).

Usage: cont18i_fieldkey_audit.py <apk> [focus_class] [hunt_name]
"""
import sys, zipfile, struct
from collections import defaultdict

APK = sys.argv[1] if len(sys.argv) > 1 else \
    'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
FOCUS = sys.argv[2] if len(sys.argv) > 2 else 'Lnb0;'
NAME_HUNT = sys.argv[3] if len(sys.argv) > 3 else 'j'

z = zipfile.ZipFile(APK)

def parse_dex(d):
    str_size, str_off = struct.unpack_from('<II', d, 56)
    type_size, type_off = struct.unpack_from('<II', d, 64)
    field_size, field_off = struct.unpack_from('<II', d, 80)
    class_size, class_off = struct.unpack_from('<II', d, 96)

    def uleb(off):
        r = 0; s = 0
        while True:
            x = d[off]; off += 1
            r |= (x & 0x7f) << s
            if not x & 0x80: return r, off
            s += 7

    def cstr(idx):
        off = struct.unpack_from('<I', d, str_off + 4 * idx)[0]
        r, off = uleb(off)
        end = d.index(b'\x00', off)
        return d[off:end].decode('utf-8', 'replace')

    def typ(idx):
        return cstr(struct.unpack_from('<I', d, type_off + 4 * idx)[0])

    def field_id(idx):
        ci, ti, ni = struct.unpack_from('<HHI', d, field_off + 8 * idx)
        return typ(ci), typ(ti), cstr(ni)

    out = {}
    bad = 0
    for i in range(class_size):
        off = class_off + 32 * i
        class_idx, access, super_idx, _ = struct.unpack_from('<IIII', d, off)
        desc = typ(class_idx)
        super_desc = typ(super_idx) if super_idx != 0xffffffff else ''
        cd_off = struct.unpack_from('<I', d, off + 24)[0]
        fl = []
        if cd_off:
            try:
                sf, p = uleb(cd_off)
                inf, p = uleb(p)
                dm, p = uleb(p)
                vm, p = uleb(p)
                fidx = 0  # per-list restart (dex_parser.cpp parity, spec: first
                          # element of a list is direct; diffs are within-list)
                for _ in range(sf):
                    fid, _acc = uleb(p); _, p = uleb(p)
                    fidx += fid
                fidx = 0
                for _ in range(inf):
                    fid, _acc = uleb(p); _, p = uleb(p)
                    fidx += fid
                    if fidx >= field_size:
                        raise ValueError(f'inst fidx {fidx} >= {field_size}')
                    _cls, fty, fname = field_id(fidx)
                    fl.append((fname, fty))
                midx = 0
                for _ in range(dm + vm):
                    _, p = uleb(p)  # method idx diff
                    _, p = uleb(p)  # access
                    _, p = uleb(p)  # code off
            except Exception:
                bad += 1
                continue
        out[desc] = {'super': super_desc, 'ifields': fl}
    if bad:
        print(f"  !! {bad}/{class_size} classes skipped (class_data walk)")
    return out

info = {}
for dexname in [n for n in z.namelist() if n.endswith('.dex')]:
    d = z.read(dexname)
    try:
        for k, v in parse_dex(d).items():
            v['dex'] = dexname
            info[k] = v
    except Exception as e:
        print(f"!! dex {dexname} parse error: {e}")

print(f"classes parsed: {len(info)}")

def chain(desc):
    out = []
    seen = set()
    while desc and desc in info and desc not in seen:
        out.append(desc)
        seen.add(desc)
        desc = info[desc]['super']
    return out

if FOCUS in info:
    print(f"\n== chain of {FOCUS}:")
    for c in chain(FOCUS):
        fl = info[c]['ifields']
        print(f"  {c}  (dex={info[c]['dex']}, ifields={len(fl)})")
        for n, t in fl:
            print(f"      {n} : {t}")
else:
    print(f"\n!! {FOCUS} not found in DEX")

print("\n== COLLAPSE FAMILY (class declares >=2 ifields same name, diff type):")
hits = 0
for desc, rec in sorted(info.items()):
    byname = defaultdict(list)
    for n, t in rec['ifields']:
        byname[n].append(t)
    dups = {n: ts for n, ts in byname.items() if len(set(ts)) >= 2}
    if dups:
        hits += 1
        if hits <= 40:
            print(f"  {desc}:")
            for n, ts in sorted(dups.items()):
                print(f"     {n} : {sorted(set(ts))}")
print(f"  total classes with intra-class name/type dups: {hits}")

print(f"\n== classes declaring ifield named '{NAME_HUNT}' (first 30):")
n_hit = 0
for desc, rec in sorted(info.items()):
    for n, t in rec['ifields']:
        if n == NAME_HUNT:
            n_hit += 1
            if n_hit <= 30:
                print(f"  {desc}  {n} : {t}")
            break
print(f"  total: {n_hit}")
