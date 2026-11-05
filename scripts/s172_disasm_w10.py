#!/usr/bin/env python3
"""s172_disasm_w10.py — S172 W10 decode: Fragment$$ExternalSyntheticLambda0
(the EXC-UNCAUGHT-TOP NPE at invoke_pc=0xf5, run_s170_w9/tb_new.err row 12)
+ j$/time/ZoneOffset (coder-named W10 partner, ASE on THEIR line only)."""
import struct
import sys
import zipfile

sys.path.insert(0, '/home/z/my-project/scripts')
from s169_disasm import OPS, opname, disasm, APK
from cont9_dexdump import Dex

TARGETS = [
    ('Landroidx/fragment/app/Fragment$$ExternalSyntheticLambda0;', None, None),
    ('Lj$/time/ZoneOffset;', '<init>', None),
]


def main():
    z = zipfile.ZipFile(APK)
    dex_names = sorted(n for n in z.namelist()
                       if n.startswith('classes') and n.endswith('.dex'))
    for cls, mname, md_want in TARGETS:
        found = False
        for dname in dex_names:
            dex_bytes = z.read(dname)
            d = Dex(dex_bytes)
            cdef = d.find_class(cls)
            if cdef is None:
                continue
            found = True
            info = d.class_methods(cdef)
            print(f"===== {cls} ({dname}) =====")
            for kind in ('direct', 'virtual'):
                for (mn, md, acc, sz, code) in info[kind]:
                    if mname is not None and mn != mname:
                        continue
                    if md_want is not None and md_want not in md:
                        continue
                    print(f"-- {kind} {mn}{md} acc=0x{acc:x} code_off=0x{code:x} size={sz}")
            # full disasm of every selected method
            for kind in ('direct', 'virtual'):
                for (mn, md, acc, sz, code) in info[kind]:
                    if mname is not None and mn != mname:
                        continue
                    disasm(d, dex_bytes, cls, mn, md)
        if not found:
            print(f"[NOT FOUND] {cls} in any dex")
    print("done")


if __name__ == '__main__':
    main()
