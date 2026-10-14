#!/usr/bin/env python3
"""cont64_w1_hxref.py v2 — fast field-op xref. Range walk stores method_idx
only (no proto decode in the hot loop); matched methods resolved lazily.
Usage: cont64_w1_hxref.py [field_id]   (default 2115 = Lel0;.h)
"""
import zipfile, struct, bisect, importlib.util, sys

spec = importlib.util.spec_from_file_location(
    "c9", "/home/z/my-project/scripts/cont9_dexdump.py")
c9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
FIELD_OPS = {0x52: 'iget', 0x53: 'iget-wide', 0x54: 'iget-object',
             0x55: 'iget-boolean', 0x59: 'iput', 0x5A: 'iput-wide',
             0x5B: 'iput-object'}

z = zipfile.ZipFile(APK)
raw = z.read('classes.dex')
d = c9.Dex(raw)
fid = int(sys.argv[1]) if len(sys.argv) > 1 else 2115

# fast code-range walk: (insns_start, insns_end, method_idx)
ranges = []
midx_walk = 0
for ci in range(d.class_defs_size):
    off = d.class_defs_off + ci * 32
    cls_idx = d.u(off, 4)
    cdo = d.u(off + 24, 4)
    if not cdo:
        continue
    p = cdo
    sf, p = d.uleb(p)
    inf, p = d.uleb(p)
    dm, p = d.uleb(p)
    vm, p = d.uleb(p)

    def skip_f(p, n):
        for _ in range(n):
            _, p = d.uleb(p)
            _, p = d.uleb(p)
        return p
    p = skip_f(p, sf + inf)
    midx = 0
    for count in (dm, vm):
        for _ in range(count):
            dd, p = d.uleb(p)
            midx += dd
            _, p = d.uleb(p)
            code, p = d.uleb(p)
            if not code:
                continue
            insns_size = d.u(code + 12, 4)
            ranges.append((code + 16, code + 16 + insns_size * 2, midx, cls_idx))
    if ci % 500 == 0:
        print(f"walk ci={ci} ranges={len(ranges)}", flush=True)
ranges.sort()
starts = [r[0] for r in ranges]
print(f"walk done: {len(ranges)} code ranges", flush=True)

needle = struct.pack('<H', fid)
pos = 0
hits = {}
while True:
    k = raw.find(needle, pos)
    if k < 0:
        break
    pos = k + 1
    if k < 2:
        continue
    opb = raw[k - 2]
    if opb not in FIELD_OPS:
        continue
    i = bisect.bisect_right(starts, k - 2) - 1
    if i < 0:
        continue
    r = ranges[i]
    if not (r[0] <= k - 2 < r[1]):
        continue
    key = (r[3], r[2], FIELD_OPS[opb])
    hits[key] = hits.get(key, 0) + 1

print(f"== field_id {fid} xref:")
for (cls_idx, midx, op), n in sorted(hits.items()):
    cls = d.type_str(cls_idx)
    mr = d.method_ref(midx)
    print(f"   {op:14s} {cls}.{mr[1]}  x{n}")
