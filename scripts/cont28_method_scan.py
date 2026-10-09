#!/usr/bin/env python3
"""cont28_method_scan.py — find ALL methods matching a name (optionally
filtered by class-prefix substring) across all DEX files of an APK.
usage: cont28_method_scan.py <apk> <method-name> [class-substring]
"""
import sys, zipfile
sys.path.insert(0, "/home/z/my-project/scripts")
from cont28_disasm import Dex

def main():
    apk, name = sys.argv[1], sys.argv[2]
    sub = sys.argv[3] if len(sys.argv) > 3 else ""
    z = zipfile.ZipFile(apk)
    for n in z.namelist():
        if not n.endswith(".dex"): continue
        dx = Dex(n, z.read(n))
        for cls, cd in dx.classes():
            if sub and sub not in cls: continue
            for msig, co in dx.method_code(cd):
                mname = msig.split(";.")[1].split("(")[0]
                if mname == name:
                    print(f"[{n}] {msig}")

if __name__ == "__main__":
    main()
