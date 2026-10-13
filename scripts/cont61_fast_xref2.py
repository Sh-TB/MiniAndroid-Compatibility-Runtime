#!/usr/bin/env python3
"""cont61_fast_xref2.py — C-speed invoke xref: bytes.find for the target
method_idx u16 pattern, opcode check on the preceding unit, attribution via
collected code ranges. Usage: cont61_fast_xref2.py <apk> <Ldesc;> <method>
"""
import sys, zipfile, importlib.util, struct

spec = importlib.util.spec_from_file_location(
    "c9", "/home/z/my-project/scripts/cont9_dexdump.py")
c9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c9)

INVOKE_OPS = set(range(0x6e, 0x73)) | set(range(0x74, 0x79))
OPNAMES = {0x6e: 'invoke-virtual', 0x6f: 'invoke-super', 0x70: 'invoke-direct',
           0x71: 'invoke-static', 0x72: 'invoke-interface',
           0x74: 'invoke-virtual/range', 0x75: 'invoke-super/range',
           0x76: 'invoke-direct/range', 0x77: 'invoke-static/range',
           0x78: 'invoke-interface/range'}


def scan(apk, tcls, tmeth, maxhits=40):
    z = zipfile.ZipFile(apk)
    pat_t = tcls if tcls.endswith(";") else tcls + ";"
    for dn in sorted(n for n in z.namelist()
                     if n.startswith("classes") and n.endswith(".dex")):
        raw = z.read(dn)
        d = c9.Dex(raw)
        # 1. target method_idx
        tgt = None
        import time as _t
        _t0 = _t.time()
        for i in range(d.method_ids_size):
            base = d.method_ids_off + i * 8
            cidx = struct.unpack_from('<H', raw, base)[0]
            nidx = struct.unpack_from('<I', raw, base + 4)[0]
            if d.string(nidx) == tmeth and d.type_str(cidx) == pat_t:
                tgt = i
                break
        print("%s: target idx=%s scanned %d method_ids in %.1fs" %
              (dn, tgt, d.method_ids_size, _t.time() - _t0), flush=True)
        if tgt is None:
            continue
        needle = struct.pack('<H', tgt)
        # 2. collect code ranges
        import time as _t
        _t1 = _t.time()
        ranges = []  # (insns_off, insns_end, cls, mname, mdesc)
        for ci in range(d.class_defs_size):
            if ci % 2000 == 0:
                print("  walk ci=%d/%d %.1fs ranges=%d" %
                      (ci, d.class_defs_size, _t.time() - _t1, len(ranges)),
                      flush=True)
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
                    insns_off = code + 16
                    ranges.append((insns_off, insns_off + insns_size * 2,
                                   cls, mr[1], mr[2]))
        ranges.sort()
        starts = [r[0] for r in ranges]
        import bisect
        # 3. bytes.find scan
        hits = 0
        pos = 0
        while True:
            k = raw.find(needle, pos)
            if k < 0:
                break
            pos = k + 1
            if k < 2:
                continue
            opb = raw[k - 2]
            if opb in INVOKE_OPS:
                i = bisect.bisect_right(starts, k) - 1
                if i >= 0:
                    s, e, cls, mn, md = ranges[i]
                    if s <= k < e:
                        print("%s -> %s%s : %s pc=%d" %
                              (cls, mn, md, OPNAMES[opb], (k - 2 - s) // 2))
                        hits += 1
                        if hits >= maxhits:
                            print("TOTAL(capped)", hits)
                            return
        if hits:
            print("-- %s done, %d hits" % (dn, hits))
    print("TOTAL", hits if 'hits' in dir() else 0)


if __name__ == "__main__":
    scan(sys.argv[1], sys.argv[2], sys.argv[3],
         int(sys.argv[4]) if len(sys.argv) > 4 else 40)
