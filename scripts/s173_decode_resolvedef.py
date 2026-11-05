#!/usr/bin/env python3
"""s173_decode_resolvedef.py — disasm Lorg/slf4j/event/EventRecodingLogger;
(R8 merge host for Koin InstanceRegistry/ScopeRegistry internals) —
resolveDefinition$koin_core and neighbors; plus Koin Scope.resolveInstance."""
import sys
import zipfile

sys.path.insert(0, '/home/z/my-project/scripts')
from s169_disasm import disasm
from cont9_dexdump import Dex

APK = '/home/z/my-project/upload/net.thunderbird.android_33.apk'


def dump(z, cls, only=None, maxmethods=None):
    for n in sorted(x for x in z.namelist()
                    if x.startswith('classes') and x.endswith('.dex')):
        b = z.read(n)
        d = Dex(b)
        cdef = d.find_class(cls)
        if cdef is None:
            continue
        info = d.class_methods(cdef)
        print(f"===== {cls} ({n}) =====")
        rows = []
        for kind in ('direct', 'virtual'):
            for (mn, md, acc, sz, code) in info[kind]:
                rows.append((kind, mn, md, acc, sz, code))
        for (kind, mn, md, acc, sz, code) in rows:
            mark = '' if only is None or any(o in mn for o in only) else ' (skip)'
            print(f"-- {kind} {mn}{md} acc=0x{acc:x} code_off=0x{code:x}"
                  f" units={sz}{mark}")
        shown = 0
        for (kind, mn, md, acc, sz, code) in rows:
            if only is not None and not any(o in mn for o in only):
                continue
            if maxmethods is not None and shown >= maxmethods:
                continue
            shown += 1
            print(f"\n### {cls}.{mn}{md} [{kind}]")
            disasm(d, b, cls, mn, md)
        return
    print(f"[NOT FOUND] {cls}")


def main():
    z = zipfile.ZipFile(APK)
    dump(z, 'Lorg/slf4j/event/EventRecodingLogger;',
         only=['resolveDefinition', 'index', 'createScope', 'getInstances'],
         maxmethods=8)
    print("\n\n########## Scope.resolveInstance ##########")
    dump(z, 'Lorg/koin/core/scope/Scope;', only=['resolveInstance'],
         maxmethods=2)
    print("done")


if __name__ == '__main__':
    main()
