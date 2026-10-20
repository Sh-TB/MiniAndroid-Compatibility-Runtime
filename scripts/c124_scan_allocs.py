#!/usr/bin/env python3
"""CONT-124: scan an APK DEX for new-instance / new-array / filled-new-array
sites targeting given type descriptors (ground truth for allocation-class
confusion decode). Uses the EXP-051 dumper's opcode size table."""
import sys, zipfile
sys.path.insert(0, "/home/z/my-project/miniandroid/tools")
import dump_method_bytecode as d


def main():
    apk = sys.argv[1]
    targets = set(sys.argv[2:])
    z = zipfile.ZipFile(apk)
    dexes = [n for n in z.namelist() if n.endswith('.dex')]
    hits = []
    for dn in dexes:
        dx = d.DexFile(z.read(dn), dn)
        for cls in dx.classes:
            if not cls.get("class_data_off"):
                continue
            for kind in ("direct_methods", "virtual_methods"):
                for m in cls["methods"][kind]:
                    coff = m["code_off"]
                    if not coff:
                        continue
                    try:
                        insns_sz = dx._u32(coff + 12)
                    except Exception:
                        continue
                    base = coff + 16
                    pc = 0
                    while pc < insns_sz:
                        op_off = base + pc * 2
                        op = dx.data[op_off] | (dx.data[op_off + 1] << 8)
                        opl = op & 0xFF
                        sz = d.get_size(opl, dx.data, op_off)
                        if sz <= 0:
                            break
                        if opl == 0x22 and sz >= 2:  # new-instance
                            tidx = dx._u16(op_off + 2)
                            desc = dx.get_type_descriptor(tidx)
                            if desc in targets:
                                cname, mname = dx.get_method_descriptor(m["method_idx"])
                                hits.append(f'new-instance {desc} in {cname}.{mname}')
                        elif opl == 0x23 and sz >= 2:  # new-array
                            tidx = dx._u16(op_off + 2)
                            desc = dx.get_type_descriptor(tidx)
                            if desc in targets or desc.startswith('[') and desc[1:] in targets:
                                cname, mname = dx.get_method_descriptor(m["method_idx"])
                                hits.append(f'new-array {desc} in {cname}.{mname}')
                        pc += sz
    for h in hits:
        print(h)
    print('total', len(hits))


if __name__ == '__main__':
    main()
