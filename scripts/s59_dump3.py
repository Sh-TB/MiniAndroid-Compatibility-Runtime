#!/usr/bin/env python3
"""
scripts/s59_dump3.py — MainActivity.onCreate + ancestor activity chain + the
setTag(key=None) sites (sget-loaded keys?).
"""
import sys, os, zipfile, tempfile, shutil
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = "/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk"

def load():
    tmp = tempfile.mkdtemp(prefix="s59d3_")
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
        classes = {c.get_name(): c for c in d.get_classes()}

        # 1. MainActivity chain
        cur = "Lio/github/yamin8000/dooz/ui/MainActivity;"
        chain = []
        while cur and cur in classes:
            c = classes[cur]
            chain.append(cur)
            cur = c.get_superclassname()
        print("== MainActivity superclass chain ==")
        for i, n in enumerate(chain):
            print(f"  {i}: {n}")

        # 2. dump onCreate of each ancestor (chain up to 5) + MainActivity.onCreate
        for i, n in enumerate(chain[:6]):
            c = classes[n]
            for m in c.get_methods():
                if m.get_name() != "onCreate":
                    continue
                print(f"\n======== {n}->onCreate{m.get_descriptor()} ========")
                code = m.get_code()
                if not code:
                    print("  (no code)")
                    continue
                pc = 0
                for ins in code.get_bc().get_instructions():
                    print(f"  @{pc:#06x} {ins.get_name()} {ops_str(ins)}")
                    pc += ins.get_length()

        # 3. setTag key=None sites from census: dump those methods
        for cls, mname in [("La72;", "a"), ("Lh32;", "a"), ("Lnh1;", "q")]:
            c = classes.get(cls)
            if not c:
                continue
            for m in c.get_methods():
                if m.get_name() != mname:
                    continue
                body = m.get_code()
                if not body:
                    continue
                txt = []
                pc = 0
                has_settag = False
                for ins in body.get_bc().get_instructions():
                    s = f"  @{pc:#06x} {ins.get_name()} {ops_str(ins)}"
                    if "setTag" in s:
                        has_settag = True
                    txt.append(s)
                    pc += ins.get_length()
                if has_settag:
                    print(f"\n======== {cls}->{mname}{m.get_descriptor()} ========")
                    print("\n".join(txt[:90]))
        return 0

if __name__ == "__main__":
    sys.exit(main())
