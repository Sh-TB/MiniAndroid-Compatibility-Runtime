#!/usr/bin/env python3
"""s173_decode_ffmodule.py — decode the TB core FeatureFlagModule DSL lambda
(FeatureFlagModuleKt$$ExternalSyntheticLambda0) — find the BaseCatalog
registrations and whether an ':inmemory:' variant exists and is guarded."""
import sys
import zipfile

sys.path.insert(0, '/home/z/my-project/scripts')
from s169_disasm import disasm
from cont9_dexdump import Dex

APK = '/home/z/my-project/upload/net.thunderbird.android_33.apk'


def dump(z, cls, only=None):
    for n in sorted(x for x in z.namelist()
                    if x.startswith('classes') and x.endswith('.dex')):
        b = z.read(n)
        d = Dex(b)
        cdef = d.find_class(cls)
        if cdef is None:
            continue
        info = d.class_methods(cdef)
        print(f"===== {cls} ({n}) =====")
        for kind in ('direct', 'virtual'):
            for (mn, md, acc, sz, code) in info[kind]:
                if only is not None and mn not in only:
                    continue
                print(f"-- {kind} {mn}{md} acc=0x{acc:x} "
                      f"code_off=0x{code:x} units={sz}")
        for kind in ('direct', 'virtual'):
            for (mn, md, acc, sz, code) in info[kind]:
                if only is not None and mn not in only:
                    continue
                print(f"\n### {cls}.{mn}{md}")
                disasm(d, b, cls, mn, md)
        return
    print(f"[NOT FOUND] {cls}")


def main():
    z = zipfile.ZipFile(APK)
    dump(z, 'Lnet/thunderbird/core/featureflag/inject/FeatureFlagModuleKt$$ExternalSyntheticLambda0;')
    print("\n\n########## InjectQualifier ##########")
    dump(z, 'Lnet/thunderbird/core/featureflag/inject/qualifier/InjectQualifier;')
    print("done")


if __name__ == '__main__':
    main()
