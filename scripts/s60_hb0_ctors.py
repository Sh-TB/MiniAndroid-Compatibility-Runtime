#!/usr/bin/env python3
"""
scripts/s60_hb0_ctors.py — R-NEW-380 (S60): Lhb0; (the R8-renamed app ViewModel)
ctor surface + Luf1;.a (the factory's ctor-matching helper) + Lo9; header.
Ground truth for: does GameViewModel have a PUBLIC no-arg ctor that Leo;.n
should have found and run?
"""
import sys, os, zipfile, tempfile, shutil
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = "/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk"

WANT = {
    "Lhb0;": {"<init>", "h", "i"},      # the app ViewModel: ctors + key fields
    "Lo9;": None,                        # AndroidViewModel header
    "Luf1;": {"a", "b"},                 # ctor-matching helper (uf1.a(Class,List))
    "Lq32;": None,                       # ViewModel header
}

def ops_str(ins):
    parts = []
    for o in ins.get_operands():
        parts.append(f"v{o[1]}" if o[0] == 0 else str(o[2] if len(o) >= 3 else o[1]))
    return ", ".join(parts)

def load():
    tmp = tempfile.mkdtemp(prefix="s60hb0_")
    ps = []
    with zipfile.ZipFile(APK) as z:
        for n in z.namelist():
            if n.startswith("classes") and n.endswith(".dex"):
                p = os.path.join(tmp, os.path.basename(n))
                with z.open(n) as f, open(p, "wb") as g:
                    shutil.copyfileobj(f, g)
                ps.append(p)
    return ps

def main():
    for p in load():
        d = DalvikVMFormat(open(p, "rb").read())
        for c in d.get_classes():
            n = c.get_name()
            if n not in WANT:
                continue
            want = WANT[n]
            print(f"\n======== {n} super={c.get_superclassname()} "
                  f"ifaces={[i.get_name() for i in c.get_interfaces()][:8]} "
                  f"access={hex(c.get_access_flags())} ========")
            for f2 in c.get_fields():
                print(f"   FIELD {f2.get_name()} {f2.get_descriptor()} access={hex(f2.get_access_flags())}")
            if want is None:
                continue
            for m in c.get_methods():
                if m.get_name() not in want:
                    continue
                print(f"--- {m.get_name()}{m.get_descriptor()} access={hex(m.get_access_flags())}")
                code = m.get_code()
                if not code:
                    print("  (abstract)")
                    continue
                pc = 0
                for ins in code.get_bc().get_instructions():
                    print(f"  @0x{pc:04x} {ins.get_name()} {ops_str(ins)}")
                    pc += ins.get_length()
    return 0

if __name__ == "__main__":
    sys.exit(main())
