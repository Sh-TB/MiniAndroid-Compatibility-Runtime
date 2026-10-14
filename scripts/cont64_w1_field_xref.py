#!/usr/bin/env python3
"""cont64_w1_field_xref.py — field-op xref for Lel0;.h (the packed
Constraints Long) and the Lel0; position/size candidates. Finds every
iget-wide/iput-wide referencing a field and attributes it to the method.
Usage: cont64_w1_field_xref.py <Lcls;> <field1> [field2 ...]
"""
import sys, zipfile, struct, bisect, importlib.util

spec = importlib.util.spec_from_file_location(
    "c9", "/home/z/my-project/scripts/cont9_dexdump.py")
c9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
WIDE_FIELD_OPS = {0x53: 'iget-wide', 0x5A: 'iput-wide'}  # 22b: op vAA vBB field@CCCC
NARROW_FIELD_OPS = {0x52: 'iget', 0x54: 'iget-object', 0x59: 'iput',
                    0x5B: 'iput-object', 0x55: 'iget-boolean'}


def field_ids_for(d, raw, cls, names):
    want = {n: None for n in names}
    for i in range(d.field_ids_size):
        base = d.field_ids_off + i * 8
        cidx = struct.unpack_from('<H', raw, base)[0]
        nidx = struct.unpack_from('<I', raw, base + 4)[0]
        nm = d.string(nidx)
        if d.type_str(cidx) == cls and nm in want:
            want[nm] = i
    return want


def code_ranges(d, raw):
    ranges = []
    for ci in range(d.class_defs_size):
        off = d.class_defs_off + ci * 32
        cls = d.type_str(d.u(off, 4))
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
        for kind, count in (("d", dm), ("v", vm)):
            for _ in range(count):
                dd, p = d.uleb(p)
                midx += dd
                _, p = d.uleb(p)
                code, p = d.uleb(p)
                if not code:
                    continue
                mr = d.method_ref(midx)
                insns_size = d.u(code + 12, 4)
                ranges.append((code + 16, code + 16 + insns_size * 2,
                               cls, mr[1]))
    ranges.sort()
    return ranges


def main():
    cls = sys.argv[1]
    if not cls.endswith(";"):
        cls += ";"
    names = sys.argv[2:]
    z = zipfile.ZipFile(APK)
    for dn in sorted(n for n in z.namelist()
                     if n.startswith("classes") and n.endswith(".dex")):
        raw = z.read(dn)
        d = c9.Dex(raw)
        fids = field_ids_for(d, raw, cls, names)
        if all(v is None for v in fids.values()):
            continue
        ranges = code_ranges(d, raw)
        starts = [r[0] for r in ranges]
        for name, fid in fids.items():
            if fid is None:
                continue
            needle = struct.pack('<H', fid)
            hits = {}
            pos = 0
            while True:
                k = raw.find(needle, pos)
                if k < 0:
                    break
                pos = k + 1
                if k < 2:
                    continue
                opb = raw[k - 2]
                opn = WIDE_FIELD_OPS.get(opb) or NARROW_FIELD_OPS.get(opb)
                if not opn:
                    continue
                i = bisect.bisect_right(starts, k - 2) - 1
                if i < 0:
                    continue
                r = ranges[i]
                key = (r[2], r[3], opn)
                hits[key] = hits.get(key, 0) + 1
            print(f"== {cls}.{name} (field {fid}) in {dn}:")
            for (c, m, op), n in sorted(hits.items()):
                print(f"   {op:12s} {c}.{m}  x{n}")


if __name__ == "__main__":
    main()
