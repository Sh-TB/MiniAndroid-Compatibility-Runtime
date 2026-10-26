#!/usr/bin/env python3
"""CONT-37 — dooz compose-draw chain decode.
1) Locate Ly3; (the compose canvas wrapper issuing android-Canvas ops per
   CDW-OP) — dump its fields/ctor and every new-instance site of it.
2) Locate the AndroidCanvas-shaped class (field Landroid/graphics/Canvas;).
3) Find who constructs them and in which method; cross-reference with the
   draw dispatch chain. Static evidence for the 'canvas never constructed'
   hypothesis (CONT-10 W6 record)."""
import sys, zipfile, importlib.util, struct

spec = importlib.util.spec_from_file_location("d9", "/home/z/my-project/scripts/cont9_dexdump.py")
d9 = importlib.util.module_from_spec(spec)
sys.modules["d9"] = d9
spec.loader.exec_module(d9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"

dexes = []
z = zipfile.ZipFile(APK)
for name in [n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]:
    dexes.append((name, d9.Dex(z.read(name))))

NEW_INSTANCE = 0x22

def scan_new_instances(d, want):
    """Return list of (class_desc, method_name, method_desc, pc, target_desc)."""
    hits = []
    for i in range(d.class_defs_size):
        off = d.class_defs_off + i*32
        cls_idx = d.u(off, 4)
        cls = d.type_str(cls_idx)
        try:
            info = d.class_methods(off)
        except Exception:
            continue
        for kind in ('direct', 'virtual'):
            for mname, mdesc, acc, sz, code in info[kind]:
                if not code or sz == 0:
                    continue
                # raw scan for new-instance + the type index
                insns_off = code + 16
                insns_sz = d.u(code+12, 4)
                for pc in range(0, insns_sz):
                    o = insns_off + pc*2
                    w = d.u(o, 2)
                    if (w & 0xFF) == NEW_INSTANCE:
                        tidx = d.u(o+2, 2)
                        t = d.type_str(tidx)
                        if t in want:
                            hits.append((cls, mname, mdesc, pc, t))
    return hits

def dump_class(desc):
    for name, d in dexes:
        off = d.find_class(desc)
        if off is None:
            continue
        info = d.class_methods(off)
        print(f"== {desc} in {name}")
        print(f"   super={info['super']} ifaces={info['ifaces']}")
        for fkind, ftype, fname in info.get('fields', []):
            print(f"   field({fkind}) {ftype} {fname}")
        for kind in ('direct', 'virtual'):
            for mname, mdesc, acc, sz, code in info[kind]:
                print(f"   [{'D' if kind=='direct' else 'V'}] {mname}{mdesc} size={sz}")
        return

def main():
    # step 1: who is Ly3;?
    print("### Ly3; (compose canvas wrapper per CDW-OP callers)")
    dump_class("Ly3;")
    print()
    # step 2: find classes with an Landroid/graphics/Canvas; instance field
    print("### classes with instance field Landroid/graphics/Canvas; (top 15)")
    n = 0
    for name, d in dexes:
        for i in range(d.class_defs_size):
            off = d.class_defs_off + i*32
            cls = d.type_str(d.u(off, 4))
            try:
                info = d.class_methods(off)
            except Exception:
                continue
            fs = [f for f in info.get('fields', []) if f[0] == 'inst' and f[1] == 'Landroid/graphics/Canvas;']
            if fs:
                print(f"   {cls} fields={[f[2] for f in fs]} ifaces={info['ifaces'][:3]}")
                n += 1
                if n >= 15:
                    break
        if n >= 15:
            break
    print()
    # step 3: new-instance sites for Ly3;
    print("### new-instance Ly3; sites")
    for name, d in dexes:
        for (cls, mname, mdesc, pc, t) in scan_new_instances(d, {"Ly3;"}):
            print(f"   {cls}.{mname}{mdesc} pc={pc}")
    print()
    print("### new-instance Ljt1; sites (the recorded composeStopwatch name — sanity)")
    for name, d in dexes:
        for (cls, mname, mdesc, pc, t) in scan_new_instances(d, {"Ljt1;"}):
            print(f"   {cls}.{mname}{mdesc} pc={pc}")

if __name__ == "__main__":
    main()
