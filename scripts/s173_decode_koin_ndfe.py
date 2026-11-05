#!/usr/bin/env python3
"""s173_decode_koin_ndfe.py — S173: decode the TB residual Koin NDFE family
(S172 PINNED NEXT #1: "which definition is missing — DEX-decode the
Scope.get caller chain").

Targets:
 1. Lorg/koin/core/scope/Scope; — resolveFromContext (throw pc=734),
    resolveInstance, resolve, get, getOrNull (the unwind chain).
 2. Dex-wide scan: callers of Scope.getOrNull / Scope.get / Scope.resolve —
    find the app-side depth-46 site that ran during module load.
 3. BaseCatalogFeatureFlagProvider + its $$ExternalSyntheticLambda1 —
    the provider class and its registration site.
 4. FeatureFlagModule registration rows already seen:
    key "…BaseCatalogFeatureFlagProvider:local:_root_" (qualifier 'local').
"""
import struct
import sys
import zipfile

sys.path.insert(0, '/home/z/my-project/scripts')
from s169_disasm import disasm
from cont9_dexdump import Dex

APK = '/home/z/my-project/upload/net.thunderbird.android_33.apk'

SCOPE = 'Lorg/koin/core/scope/Scope;'
SCOPE_METHODS = ['resolveFromContext', 'resolveInstance', 'resolve',
                 'getOrNull', 'get', 'declareContext']

NDFE = 'Lorg/koin/core/error/NoDefinitionFoundException;'
PROVIDER = 'Lnet/thunderbird/core/featureflag/provider/BaseCatalogFeatureFlagProvider;'


def load_dexes(z):
    out = []
    for n in sorted(x for x in z.namelist()
                    if x.startswith('classes') and x.endswith('.dex')):
        b = z.read(n)
        out.append((n, b, Dex(b)))
    return out


def iter_methods(d):
    """yield (cls, kind, mn, md, acc, code_off, units) across all classes"""
    for i in range(d.class_defs_size):
        cdef = d.class_defs_off + i * 32
        desc_idx = d.u(cdef, 4)
        cls = d.type_str(desc_idx)
        try:
            info = d.class_methods(cdef)
        except Exception:
            continue
        for kind in ('direct', 'virtual'):
            for (mn, md, acc, sz, code) in info[kind]:
                yield cls, kind, mn, md, acc, code, sz


def scan_methodrefs(dexes, want_names, want_cls_sub=None):
    """find methods that invoke/call given method names (via invoke ops)"""
    hits = []
    INVOKE = {0x6e, 0x6f, 0x70, 0x71, 0x72,
              0x74, 0x75, 0x76, 0x77, 0x78}
    for (n, b, d) in dexes:
        for (cls, kind, mn, md, acc, code, sz) in iter_methods(d):
            if code == 0:
                continue
            buf = b
            off = code * 2 + 8  # skip insns_size u32? cont9 uses raw code_off*2
            # cont9 disasm uses code_off as unit offset of insns; emulate:
            insns_off = code * 2
            insns_size = sz
            pc = 0
            try:
                while pc < insns_size:
                    o = insns_off + pc * 2
                    op = buf[o]
                    if op in INVOKE:
                        idx = struct.unpack_from('<H', buf, o + 2)[0]
                        rc, rmn, rmd = d.method_ref(idx)
                        if rmn in want_names and (want_cls_sub is None
                                                  or want_cls_sub in rc):
                            hits.append((n, cls, kind, mn, md, pc,
                                         rc, rmn, rmd))
                            if len(hits) > 400:
                                return hits
                    size = 2
                    if 0x00 <= op <= 0x0f:
                        size = 2
                    elif op in (0x1a, 0x1c, 0x1d, 0x1e, 0x22,
                                0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58,
                                0x59, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f,
                                0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66,
                                0x69, 0x6a, 0x6b, 0x6c, 0x6d, 0x6e, 0x6f,
                                0x70, 0x71, 0x72, 0x20, 0x23, 0x24, 0x25,
                                0x1f, 0x13, 0x15, 0x16, 0x21c and 0):
                        size = 4
                    elif op in (0x12, 0x1e):
                        size = 2
                    else:
                        size = 2
                    pc += size // 2
            except Exception:
                pass
    return hits


def const_string_hits(dexes, needles):
    """find (dex, cls, method, pc, string) for const-string with needle"""
    hits = []
    for (n, b, d) in dexes:
        for (cls, kind, mn, md, acc, code, sz) in iter_methods(d):
            if code == 0:
                continue
            insns_off = code * 2
            pc = 0
            try:
                while pc < sz:
                    o = insns_off + pc * 2
                    op = b[o]
                    if op == 0x1a:
                        idx = struct.unpack_from('<H', b, o + 2)[0]
                        s = d.string(idx)
                        if any(x in s for x in needles):
                            hits.append((n, cls, mn, pc, s))
                    elif op == 0x1b:
                        idx = struct.unpack_from('<I', b, o + 2)[0]
                        s = d.string(idx)
                        if any(x in s for x in needles):
                            hits.append((n, cls, mn, pc, s))
                        pc += 2
                    pc += 1
            except Exception:
                pass
    return hits


def disasm_class(dexes, cls, only=None):
    for (n, b, d) in dexes:
        cdef = d.find_class(cls)
        if cdef is None:
            continue
        info = d.class_methods(cdef)
        print(f"===== {cls} ({n}) =====")
        for kind in ('direct', 'virtual'):
            for (mn, md, acc, sz, code) in info[kind]:
                if only is not None and mn not in only:
                    continue
                print(f"-- {kind} {mn}{md} acc=0x{acc:x} code_off=0x{code:x}"
                      f" units={sz}")
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
    dexes = load_dexes(z)
    print(f"loaded {len(dexes)} dex files")

    print("\n== [1] const-string scan: provider name / NDFE message ==")
    hits = const_string_hits(dexes, ['BaseCatalogFeatureFlagProvider',
                                     'No definition found',
                                     'NoDefinitionFound'])
    for (n, cls, mn, pc, s) in hits[:40]:
        print(f"  {n} {cls}.{mn} pc={pc} :: {s[:110]}")
    print(f"  total {len(hits)}")

    print("\n== [2] disasm Scope.resolveFromContext (throw pc=734) ==")
    disasm_class(dexes, SCOPE, only={'resolveFromContext'})


if __name__ == '__main__':
    main()
