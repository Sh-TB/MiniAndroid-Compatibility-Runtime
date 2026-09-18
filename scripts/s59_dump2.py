#!/usr/bin/env python3
"""
scripts/s59_dump2.py — targeted method dumps for the R-NEW-379 owner families.
Lrd1;.v (parent walk), Llo;.J/.u/.E (owner family A), Ljm;.i (setTag 2131230803),
Lxd1;.g (owner get walk) — full resolved disasm + class headers.
"""
import sys, os, zipfile, tempfile, shutil
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = "/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk"
WANT = {
    "Lrd1;": {"v"},
    "Llo;": {"J", "u", "E"},
    "Ljm;": {"i"},
    "Lxd1;": {"g"},
    "Lvo0;": None,   # header only (LifecycleOwner?)
    "Lho;": None,    # header only (the view class in the ISE)
}

def load():
    tmp = tempfile.mkdtemp(prefix="s59d2_")
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

def main():
    for p in load():
        d = DalvikVMFormat(open(p, "rb").read())
        for c in d.get_classes():
            n = c.get_name()
            if n not in WANT:
                continue
            print(f"\n======== {n} super={c.get_superclassname()} ifaces={[i.get_name() for i in c.get_interfaces()][:6]} ========")
            want = WANT[n]
            for m in c.get_methods():
                if want is not None and m.get_name() not in want:
                    continue
                print(f"--- {m.get_name()}{m.get_descriptor()}")
                code = m.get_code()
                if not code:
                    print("  (abstract)")
                    continue
                pc = 0
                for ins in code.get_bc().get_instructions():
                    print(f"  @{pc:#06x} {ins.get_name()} {ops_str(ins)}")
                    pc += ins.get_length()
        return 0

if __name__ == "__main__":
    sys.exit(main())
