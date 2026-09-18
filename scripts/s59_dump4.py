#!/usr/bin/env python3
"""
scripts/s59_dump4.py — Lmc1;.b (the suspected ViewTree owner installer), Loc1;
statics, and any method in the DEX that references type Lvo0; (LifecycleOwner)
in a check-cast/instance-of near a setTag — plus Lb81; header.
"""
import sys, os, zipfile, tempfile, shutil
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = "/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk"

def load():
    tmp = tempfile.mkdtemp(prefix="s59d4_")
    with zipfile.ZipFile(APK) as z:
        ps = []
        for n in z.namelist():
            if n.startswith("classes") and n.endswith(".dex"):
                p = os.path.join(tmp, os.path.basename(n))
                with z.open(n) as f, open(p, "wb") as g:
                    shutil.copyfileobj(f, g)
                ps.append(p)
    return ps

def ops_str(ins):
    parts = []
    for o in ins.get_operands():
        parts.append(f"v{o[1]}" if o[0] == 0 else str(o[2] if len(o) >= 3 else o[1]))
    return ", ".join(parts)

def dump_method(m, limit=200):
    code = m.get_code()
    if not code:
        print("  (no code)")
        return
    pc = 0
    for i, ins in enumerate(code.get_bc().get_instructions()):
        if i >= limit:
            print(f"  ... (truncated at {limit})")
            break
        print(f"  @{pc:#06x} {ins.get_name()} {ops_str(ins)}")
        pc += ins.get_length()

def main():
    for p in load():
        d = DalvikVMFormat(open(p, "rb").read())
        classes = {c.get_name(): c for c in d.get_classes()}

        for cls, meths in [("Lmc1;", None), ("Loc1;", None), ("Lb81;", None)]:
            c = classes.get(cls)
            if not c:
                print(f"== {cls}: NOT FOUND")
                continue
            print(f"\n======== {cls} super={c.get_superclassname()} ========")
            for f in c.get_fields():
                print(f"  FIELD {f.get_name()}:{f.get_descriptor()}")
            for m in c.get_methods():
                print(f"--- {m.get_name()}{m.get_descriptor()}")
                dump_method(m, 120)
        return 0

if __name__ == "__main__":
    sys.exit(main())
