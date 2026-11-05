#!/usr/bin/env python3
"""s172_decode_ncm_lambda.py — decode NotificationChannelManager
$r8$lambda$m3LNel5iYKrrYmwu_gXHemecIYY + the private method it calls
(the List.iterator null-recv site behind the W10 uncaught NPE)."""
import sys
import zipfile

sys.path.insert(0, '/home/z/my-project/scripts')
from s169_disasm import disasm, APK

CLS = 'Lcom/fsck/k9/notification/NotificationChannelManager;'
LAMBDA = '$r8$lambda$m3LNel5iYKrrYmwu_gXHemecIYY'


def main():
    z = zipfile.ZipFile(APK)
    for dname in sorted(n for n in z.namelist()
                        if n.startswith('classes') and n.endswith('.dex')):
        dex_bytes = z.read(dname)
        try:
            from cont9_dexdump import Dex
            d = Dex(dex_bytes)
            cdef = d.find_class(CLS)
        except Exception:
            continue
        if cdef is None:
            continue
        info = d.class_methods(cdef)
        print(f"== {CLS} in {dname} ==")
        for kind in ('direct', 'virtual'):
            for (mn, md, acc, sz, code) in info[kind]:
                if LAMBDA in mn:
                    print(f"-- {kind} {mn}{md} code_off=0x{code:x} size={sz}")
        print("=== LAMBDA BODY ===")
        disasm(d, dex_bytes, CLS, LAMBDA)
        break


if __name__ == '__main__':
    main()
