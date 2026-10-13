#!/usr/bin/env python3
"""cont61_tryitem.py — W1 (CONT-61): decode code_item try/catch tables for
the dooz CancellationException ("Flow was aborted") unwind frames.

Usage: cont61_tryitem.py <apk> "Lcls;" [method...]   (method omitted = list)
Output: per method: try ranges with handler type lists (types resolved).
"""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location(
    "c9", "/home/z/my-project/scripts/cont9_dexdump.py")
c9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c9)


def catch_list(d, code_off):
    """Return [(start, count, [types-or-ALL, addr]), ...] for a code item."""
    tries = d.u(code_off + 6, 2)
    insns_size = d.u(code_off + 12, 4)
    insns_off = code_off + 16
    # try items start after insns, 4-aligned
    tpos = insns_off + insns_size * 2
    if tpos & 3:
        tpos += 2
    out = []
    hbase = tpos + tries * 8
    for t in range(tries):
        base = tpos + t * 8
        start = d.u(base, 4)
        count = d.u(base + 4, 2)
        hoff = d.u(base + 6, 2)
        hp = hbase + hoff
        size, hp = d.sleb(hp)
        handlers = []
        if size > 0:
            for _ in range(size):
                tidx, hp = d.uleb(hp)
                addr, hp = d.uleb(hp)
                handlers.append((d.type_str(tidx), addr))
            ca, _ = d.uleb(hp)
            handlers.append(("ALL", ca))
        elif size < 0:
            for _ in range(-size):
                tidx, hp = d.uleb(hp)
                addr, hp = d.uleb(hp)
                handlers.append((d.type_str(tidx), addr))
            ca, _ = d.uleb(hp)
            handlers.append(("ALL", ca))
        else:
            ca, _ = d.uleb(hp)
            handlers.append(("ALL", ca))
        out.append((start, count, handlers))
    return out


def main():
    apk = sys.argv[1]
    cls = sys.argv[2]
    methods = sys.argv[3:] if len(sys.argv) > 3 else None
    z = zipfile.ZipFile(apk)
    dexnames = sorted(n for n in z.namelist()
                      if n.startswith("classes") and n.endswith(".dex"))
    for dn in dexnames:
        d = c9.Dex(z.read(dn))
        coff = d.find_class(cls if cls.endswith(";") else cls + ";")
        if coff is None:
            continue
        cm = d.class_methods(coff)
        print("== %s in %s" % (cls, dn))
        for kind in ("direct", "virtual"):
            for (mname, mdesc, acc, sz, code) in cm[kind]:
                if methods and mname not in methods:
                    continue
                if not code:
                    print("  %s%s abstract (no code)" % (mname, mdesc))
                    continue
                print("  %s%s size=%d" % (mname, mdesc, sz))
                try:
                    trs = catch_list(d, code)
                except Exception as e:
                    print("    <catch parse err %s>" % e)
                    trs = []
                if not trs:
                    print("    (no try items)")
                for (start, count, hs) in trs:
                    hs_s = ", ".join("%s@0x%x" % (t, a) for (t, a) in hs)
                    print("    try [0x%x..0x%x) -> %s" % (start,
                                                          start + count,
                                                          hs_s))


if __name__ == "__main__":
    main()
