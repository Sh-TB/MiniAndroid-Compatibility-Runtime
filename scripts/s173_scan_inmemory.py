#!/usr/bin/env python3
"""s173_scan_inmemory.py — find every method that (a) sgets
InjectQualifier.InMemory/Local/Remote, (b) references
BaseCatalogFeatureFlagProvider (ctor/virtual), to locate the missing
':inmemory:' registration site in the TB dex."""
import struct
import sys
import zipfile

sys.path.insert(0, '/home/z/my-project/scripts')
from s169_disasm import OPS
from cont9_dexdump import Dex

APK = '/home/z/my-project/upload/net.thunderbird.android_33.apk'

QUAL_CLS = 'Lnet/thunderbird/core/featureflag/inject/qualifier/InjectQualifier;'
PROV_CLS = 'Lnet/thunderbird/core/featureflag/provider/BaseCatalogFeatureFlagProvider;'


def main():
    z = zipfile.ZipFile(APK)
    dexes = []
    for n in sorted(x for x in z.namelist()
                    if x.startswith('classes') and x.endswith('.dex')):
        b = z.read(n)
        dexes.append((n, b, Dex(b)))

    # Pass 1: field_ids for InjectQualifier.* statics, method_ids naming
    # the provider class.
    qual_fields = {}   # fname -> [(dex, fidx)]
    prov_methods = set()  # (dex, method_idx) refs to provider methods
    for (n, b, d) in dexes:
        for fidx in range(d.field_ids_size):
            off = d.field_ids_off + fidx * 8
            cls = d.u(off, 2)
            name = d.string(d.u(off + 4, 4))
            if d.type_str(cls) == QUAL_CLS:
                qual_fields.setdefault(name, []).append((n, fidx))
        for midx in range(d.method_ids_size):
            off = d.method_ids_off + midx * 8
            cls = d.u(off, 2)
            if d.type_str(cls) == PROV_CLS:
                mn = d.string(d.u(off + 4, 4))
                prov_methods.add((n, midx, mn))
    print("InjectQualifier static fields:",
          {k: len(v) for k, v in qual_fields.items()})
    print("provider method refs:", len(prov_methods))

    # Pass 2: scan every method's code for sget (0x60..0x66) of the
    # qualifier fields and any invoke/new-instance of the provider.
    SGET_OPS = {0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66}
    NEW_OPS = {0x22}
    hits = []
    for (n, b, d) in dexes:
        fidx_by_field = {}
        for fname, lst in qual_fields.items():
            for (dn, fidx) in lst:
                if dn == n:
                    fidx_by_field[fidx] = fname
        prov_midx = {m for (dn, m, _) in prov_methods if dn == n}
        for i in range(d.class_defs_size):
            cdef = d.class_defs_off + i * 32
            try:
                cls = d.type_str(d.u(cdef, 4))
                info = d.class_methods(cdef)
            except Exception:
                continue
            for kind in ('direct', 'virtual'):
                for (mn, md, acc, sz, code) in info[kind]:
                    if code == 0:
                        continue
                    off = code + 16
                    pc = 0
                    qnames = set()
                    uses_prov = False
                    while pc < sz:
                        o = off + pc * 2
                        op = b[o]
                        ent = OPS.get(op)
                        if ent is None:
                            pc += 1
                            continue
                        size, fmt, _ = ent
                        try:
                            if op in SGET_OPS:
                                f = struct.unpack_from('<H', b, o + 2)[0]
                                if f in fidx_by_field:
                                    qnames.add(fidx_by_field[f])
                            elif op in NEW_OPS:
                                t = struct.unpack_from('<H', b, o + 2)[0]
                                if d.type_str(t) == PROV_CLS:
                                    uses_prov = True
                            elif fmt in ('35c', '45cc', '3rc', '5rc'):
                                m = struct.unpack_from('<H', b, o + 2)[0]
                                if m in prov_midx:
                                    uses_prov = True
                        except Exception:
                            pass
                        pc += max(1, size // 2)
                    if qnames or uses_prov:
                        hits.append((n, cls, kind, mn,
                                     sorted(qnames), uses_prov))

    print(f"\n{len(hits)} methods referencing qualifier statics/provider:")
    for (n, cls, kind, mn, qs, up) in hits:
        tag = 'PROV' if up else '    '
        print(f"  [{tag}] {cls};.{mn} qualifiers={qs}")


if __name__ == '__main__':
    main()
