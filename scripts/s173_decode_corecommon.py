#!/usr/bin/env python3
"""s173_decode_corecommon.py — S173: decode CoreCommonModuleKt +
$$ExternalSyntheticLambda1 (the depth-46 getOrNull site in the TB residual
Koin NDFE) and the GeneralSettingsManager registration row."""
import sys
import zipfile

sys.path.insert(0, '/home/z/my-project/scripts')
from s169_disasm import disasm
from cont9_dexdump import Dex

APK = '/home/z/my-project/upload/net.thunderbird.android_33.apk'

TARGETS = [
    'Lnet/thunderbird/core/common/CoreCommonModuleKt;',
    'Lnet/thunderbird/core/common/CoreCommonModuleKt$$ExternalSyntheticLambda1;',
    'Lnet/thunderbird/core/common/CoreCommonModuleKt$$ExternalSyntheticLambda0;',
]


def main():
    z = zipfile.ZipFile(APK)
    for n in sorted(x for x in z.namelist()
                    if x.startswith('classes') and x.endswith('.dex')):
        b = z.read(n)
        d = Dex(b)
        for cls in TARGETS:
            cdef = d.find_class(cls)
            if cdef is None:
                continue
            info = d.class_methods(cdef)
            print(f"===== {cls} ({n}) =====")
            for kind in ('direct', 'virtual'):
                for (mn, md, acc, sz, code) in info[kind]:
                    print(f"-- {kind} {mn}{md} acc=0x{acc:x} "
                          f"code_off=0x{code:x} units={sz}")
            for kind in ('direct', 'virtual'):
                for (mn, md, acc, sz, code) in info[kind]:
                    print(f"\n### {cls}.{mn}{md}")
                    disasm(d, b, cls, mn, md)
    print("done")


if __name__ == '__main__':
    main()
