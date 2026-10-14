#!/usr/bin/env python3
"""cont61_fast_xref.py — fast invoke cross-reference via raw u16 insn scan.
Usage: cont61_fast_xref.py <apk> <Ltargetdesc;> <method-name> [maxhits]
Prints caller class.method -> opcode, by scanning every code item's insn
array for invoke opcodes (0x6e-0x72, 0x74-0x78) whose operand index maps
to the target (class,name) pair in method_ids.
"""
import sys, zipfile, importlib.util, struct

spec = importlib.util.spec_from_file_location(
    "c9", "/home/z/my-project/scripts/cont9_dexdump.py")
c9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c9)

INVOKE_OPS = set(range(0x6e, 0x73)) | set(range(0x74, 0x79))


def scan(apk, tcls, tmeth, maxhits=40):
    z = zipfile.ZipFile(apk)
    dexnames = sorted(n for n in z.namelist()
                      if n.startswith("classes") and n.endswith(".dex"))
    hits = 0
    for dn in dexnames:
        raw = z.read(dn)
        d = c9.Dex(raw)
        # 1. find target method_idx in method_ids
        tgt_idx = None
        mid_off = d.method_ids_off
        for i in range(d.method_ids_size):
            base = mid_off + i * 8
            cidx = struct.unpack_from('<H', raw, base)[0]
            mname_idx = struct.unpack_from('<I', raw, base + 4)[0]
            if d.string(mname_idx) == tmeth:
                desc = d.type_str(cidx)
                if desc == tcls or desc == tcls + ";":
                    tgt_idx = i
                    break
        if tgt_idx is None:
            print("%s: target not found" % dn)
            continue
        # 2. walk class_defs -> methods -> code ranges; raw-scan insns
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
            for kind, count in (("direct", dm), ("virtual", vm)):
                for _ in range(count):
                    dd, p = d.uleb(p)
                    midx += dd
                    _, p = d.uleb(p)
                    code, p = d.uleb(p)
                    if not code:
                        continue
                    mname, mdesc = d.method_ref(midx)[1], d.method_ref(midx)[2]
                    insns_size = d.u(code + 12, 4)
                    insns_off = code + 16
                    # raw u16 scan
                    prev_op = 0
                    for u in range(insns_size):
                        w = d.u(insns_off + u * 2, 2)
                        op = w & 0xff
                        # 10x ops carry method idx at operand B (next unit)
                        if op in INVOKE_OPS and u + 1 < insns_size:
                            mi = d.u(insns_off + (u + 1) * 2, 2)
                            if mi == tgt_idx:
                                # disassemble around the hit site for context
                                print("%s -> %s%s : op%#x pc=%d" %
                                      (cls, mname, mdesc, op, u))
                                hits += 1
                                if hits >= maxhits:
                                    return
    print("TOTAL", hits)


if __name__ == "__main__":
    apk, tcls, tmeth = sys.argv[1], sys.argv[2], sys.argv[3]
    mh = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    scan(apk, tcls, tmeth, mh)
