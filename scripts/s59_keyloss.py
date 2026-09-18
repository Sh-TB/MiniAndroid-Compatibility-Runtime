#!/usr/bin/env python3
"""
scripts/s59_keyloss.py — dump Lwl0;.containsKey, Lyd0;.b, Lu32;.c, Lt3;.q (pc
window around 109/11/27) to trace the lost Class key.
"""
import sys, os, zipfile, tempfile, shutil
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = "/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk"
WANT = {
    "Lwl0;": {"containsKey"},
    "Lyd0;": {"b"},
    "Lu32;": {"c"},
}

def load():
    tmp = tempfile.mkdtemp(prefix="s59kl_")
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

def dump(m, limit_pc=None, window=0):
    code = m.get_code()
    if not code:
        print("  (no code)")
        return
    pc = 0
    for i, ins in enumerate(code.get_bc().get_instructions()):
        if limit_pc is None or abs(pc - limit_pc) <= window:
            print(f"  @{pc:#06x} {ins.get_name()} {ops_str(ins)}")
        pc += ins.get_length()

def main():
    for p in load():
        d = DalvikVMFormat(open(p, "rb").read())
        for cls, meths in WANT.items():
            for c in d.get_classes():
                if c.get_name() != cls:
                    continue
                print(f"\n======== {cls} super={c.get_superclassname()} ========")
                for m in c.get_methods():
                    if m.get_name() not in meths:
                        continue
                    print(f"--- {m.get_name()}{m.get_descriptor()}")
                    dump(m)
        # Lt3;.q — window around pc 109 and head
        for c in d.get_classes():
            if c.get_name() != "Lt3;":
                continue
            for m in c.get_methods():
                if m.get_name() != "q":
                    continue
                print(f"\n--- Lt3;.q{m.get_descriptor()} [head 0..60] ---")
                code = m.get_code()
                pc = 0
                for i, ins in enumerate(code.get_bc().get_instructions()):
                    if pc < 60 or (0x50 <= pc <= 0x90):
                        print(f"  @{pc:#06x} {ins.get_name()} {ops_str(ins)}")
                    pc += ins.get_length()
        return 0

if __name__ == "__main__":
    sys.exit(main())
