#!/usr/bin/env python3
"""s122_dump_gcy.py — dump Lg/c0;.y bytecode around pc=456 (chess NPE probe).
Uses the repo's dump_method_bytecode DexFile parser; skips undecodable ops."""
import io
import struct
import sys
import zipfile

sys.path.insert(0, "/home/z/my-project/miniandroid/tools")
import dump_method_bytecode as dmb  # noqa: E402


def main():
    apk = sys.argv[1]
    cls = sys.argv[2]
    meth = sys.argv[3]
    target_pc = int(sys.argv[4]) if len(sys.argv) > 4 else 456
    with zipfile.ZipFile(apk) as z:
        for name in sorted(n for n in z.namelist() if n.endswith(".dex")):
            data = z.read(name)
            try:
                dex = dmb.DexFile(data, name)
            except Exception:
                continue
            code_off, m = dex.find_method(cls, meth)
            if code_off is None:
                continue
            print(f"=== {cls}.{meth} in {name} (insns_size={m.get('insns_size') if isinstance(m, dict) else '?'}) ===")
            insns = dex.read_code_insns(code_off)
            lo, hi = target_pc - 30, target_pc + 6
            for pc, raw, txt in insns:
                if lo <= pc <= hi:
                    print(f"PC={pc:5d}  {txt}")
            return
    print(f"{cls}.{meth}: NOT FOUND")


if __name__ == "__main__":
    main()
