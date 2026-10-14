#!/usr/bin/env python3
"""cont64_w1_ixref.py — FAST invoke-op xref (v2 walker: no proto decode in
the hot loop; matched methods resolved lazily).
Usage: cont64_w1_ixref.py <Lcls;> <method> [dexname]
"""
import zipfile, struct, bisect, importlib.util, sys

spec = importlib.util.spec_from_file_location(
    "c9", "/home/z/my-project/scripts/cont9_dexdump.py")
c9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
INVOKE_OPS = {0x6e: 'invoke-virtual', 0x6f: 'invoke-super',
              0x70: 'invoke-direct', 0x71: 'invoke-static',
              0x72: 'invoke-interface'}

cls_want = sys.argv[1]
if not cls_want.endswith(";"):
    cls_want += ";"
meth_want = sys.argv[2]

z = zipfile.ZipFile(APK)
dn_want = sys.argv[3] if len(sys.argv) > 3 else None

tgt = None
for dn in sorted(n for n in z.namelist()
                 if n.startswith("classes") and n.endswith(".dex")):
    if dn_want and dn != dn_want:
        continue
    raw = z.read(dn)
    d = c9.Dex(raw)
    for i in range(d.method_ids_size):
        base = d.method_ids_off + i * 8
        cidx = struct.unpack_from('<H', raw, base)[0]
        nidx = struct.unpack_from('<I', raw, base + 4)[0]
        if d.string(nidx) == meth_want and d.type_str(cidx) == cls_want:
            tgt = (dn, raw, d, i)
            break
    if tgt:
        break
if not tgt:
    print(f"method {cls_want}.{meth_want} NOT FOUND in method_ids")
    sys.exit(1)

dn, raw, d, mid = tgt
print(f"target {cls_want}.{meth_want} = method_id {mid} in {dn}")

ranges = []
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
ranges.sort()
starts = [r[0] for r in ranges]
print(f"walk done: {len(ranges)} ranges", flush=True)

needle = struct.pack('<H', mid)
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
    if opb not in INVOKE_OPS:
        continue
    i = bisect.bisect_right(starts, k - 2) - 1
    if i < 0:
        continue
    r = ranges[i]
    if not (r[0] <= k - 2 < r[1]):
        continue
    key = (r[3], r[2], INVOKE_OPS[opb])
    hits[key] = hits.get(key, 0) + 1

print(f"== callers of {cls_want}.{meth_want}:")
for (cls_idx, midx, op), n in sorted(hits.items()):
    cls = d.type_str(cls_idx)
    mr = d.method_ref(midx)
    print(f"   {op:16s} {cls}.{mr[1]}  x{n}")
