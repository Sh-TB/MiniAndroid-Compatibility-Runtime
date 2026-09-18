#!/usr/bin/env python3
"""
scripts/s60_r380_forensic.py — R-NEW-380 DEX ground truth (S60).
Dumps the ViewModelProvider create chain from dooz v23:
  Lyd0;.b → Ltf1;.b → Lt32;.b → Lt32;.d → Leo;.n (throws "Cannot create an instance of ")
plus GameViewModel (io.github.yamin8000.dooz GameViewModel) ctor surface and the
Factory family classes reachable from the chain.
Ground truth for: which factory step failed (ctor discovery vs newInstance dispatch
vs a stubbed dependency) and where the EMPTY class name comes from.
"""
import sys, os, zipfile, tempfile, shutil
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = "/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk"

# classes the S59 chain names; dump everything in them so we see the factory logic
WANT = {
    "Lyd0;": {"b"},
    "Ltf1;": {"b"},
    "Lt32;": {"b", "d"},
    "Leo;":  {"n"},
    "Lwl0;": {"containsKey"},
    "Lyi0;": None,   # possible ViewModelProvider (header only)
    "Loe;":  None,   # header only
    "Leu;":  None,   # header only
}

def load():
    tmp = tempfile.mkdtemp(prefix="s60r380_")
    with zipfile.ZipFile(APK) as z:
        ps = []
        for n in z.namelist():
            if n.startswith("classes") and n.endswith(".dex"):
                p = os.path.join(tmp, os.path.basename(n))
                with z.open(n) as f, open(p, "wb") as g:
                    shutil.copyfileobj(f, g)
                ps.append(p)
    return ps

def main():
    for p in load():
        with open(p, "rb") as f:
            d = DalvikVMFormat(f.read())
        for c in d.get_classes():
            name = c.get_name()
            hdr = name in WANT and WANT[name] is None
            want_m = WANT.get(name)
            if not hdr and want_m is None:
                continue
            print("=" * 78)
            print("CLASS", name, "extends", c.get_superclassname(),
                  "access", hex(c.get_access_flags()))
            if hdr:
                for f2 in c.get_fields():
                    print("   FIELD", f2.get_name(), f2.get_descriptor())
                continue
            for m in c.get_methods():
                if m.get_name() not in want_m:
                    continue
                print("-" * 78)
                print("METHOD", name, "->", m.get_name(), m.get_descriptor(),
                      "access", hex(m.get_access_flags()))
                code = m.get_code()
                if code is None:
                    print("   (abstract/native)")
                    continue
                pc = 0
                for ins in code.get_bc().get_instructions():
                    parts = []
                    for o in ins.get_operands():
                        parts.append(f"v{o[1]}" if o[0] == 0 else str(o[2] if len(o) >= 3 else o[1]))
                    print("   @0x%04x  %-22s %s" % (pc, ins.get_name(), ", ".join(parts)))
                    pc += ins.get_length()
    return 0

if __name__ == "__main__":
    sys.exit(main())
