#!/usr/bin/env python3
"""scripts/forensic/m3_find_callers.py — find ALL invoke sites of a target method in a DEX.

Usage: python3 scripts/forensic/m3_find_callers.py <apk> <class-desc> <method-name> [apk2 ...]
Reuses m3_disasm's spec-conformant format table (validated 28/30 vs
androguard) so the instruction walk stays aligned (payloads consumed).
"""
import sys, zipfile, struct
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import importlib.util
spec = importlib.util.spec_from_file_location(
    "m3dis", __file__.rsplit("/", 1)[0] + "/m3_disasm.py")
m3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m3)

INVOKE_OPS = {0x6E, 0x6F, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78}

def main():
    apk = sys.argv[1]
    cls_sub, mth = sys.argv[2], sys.argv[3]
    z = zipfile.ZipFile(apk)
    names = z.namelist()
    dexes = [n for n in names if n.startswith("classes") and n.endswith(".dex")]
    for dexname in dexes:
        d = z.read(dexname)
        u2 = lambda o: struct.unpack_from("<H", d, o)[0]
        u4 = lambda o: struct.unpack_from("<I", d, o)[0]
        def uleb(p):
            r, s = 0, 0
            while True:
                b = d[p + s]; r |= (b & 0x7F) << (7 * s); s += 1
                if not (b & 0x80): return r, p + s
        str_off = u4(0x3C); type_off = u4(0x44)
        m_off, m_sz = u4(0x5C), u4(0x58)
        c_off, c_sz = u4(0x64), u4(0x60)
        def get_str(i):
            off = u4(str_off + 4 * i)
            r, p = uleb(off)
            return d[p:p + r].split(b"\x00")[0].decode("utf-8", "replace")
        def type_of(i): return get_str(u4(type_off + 4 * i))
        def meth_of(i):
            mo = m_off + 8 * i
            return f"{type_of(u2(mo))}.{get_str(u4(mo + 4))}"
        targets = {}
        for i in range(m_sz):
            full = meth_of(i)
            if full == f"{cls_sub}.{mth}":
                targets[i] = full
        if not targets:
            continue
        print(f"[{dexname}] targets:", targets)
        for ci in range(c_sz):
            co = c_off + 32 * ci
            cls_name = type_of(u2(co))
            cdo = u4(co + 24)  # androguard-verified: class_data_off @+24 (static_values @+20)
            if cdo == 0:
                continue
            p = cdo
            sf, p = uleb(p); infld, p = uleb(p); dm, p = uleb(p); vm, p = uleb(p)
            for _ in range(sf):
                _, p = uleb(p); _, p = uleb(p)
            for _ in range(infld):
                _, p = uleb(p); _, p = uleb(p)
            dm_idx = 0
            for _ in range(dm):
                diff, p = uleb(p); _, p = uleb(p)
                dm_idx += diff
                coff, p = uleb(p)
                # code_item: regs u2, ins u2, outs u2, tries u2, debug u4,
                #            insns_size u4(+12), insns bytes at coff+16
                insns_off = coff + 16
                insns_sz = u4(coff + 12)
                caller = meth_of(dm_idx)
                pc = 0
                while pc < insns_sz:
                    w = u2(insns_off + 2 * pc)
                    op, hi = m3.decode_word(w)
                    if op == 0x00 and hi in (1, 2, 3):
                        if hi == 1:
                            size = u2(insns_off + 2*pc + 2)
                            pc += 4 + (2 * size + 1) // 2
                        elif hi == 2:
                            size = u2(insns_off + 2*pc + 2)
                            pc += 2 + 2 * size
                        else:
                            ew = u2(insns_off + 2*pc + 2)
                            cnt = u2(insns_off + 2*pc + 4)
                            pc += 4 + (ew * cnt + 1) // 2
                        continue
                    fmt = m3._S[op][1] if op in m3._S else "10x"
                    width = m3.SIZES.get(fmt, 1)
                    if op in INVOKE_OPS and pc + 2 < insns_sz:
                        midx_at = u2(insns_off + 2 * pc + 2)
                        if midx_at in targets:
                            print(f"HIT {cls_name} via {caller} pc=0x{pc:04x} "
                                  f"-> {targets[midx_at]}")
                    pc += width
    print("done")

if __name__ == "__main__":
    main()
