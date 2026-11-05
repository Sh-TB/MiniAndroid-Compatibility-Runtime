#!/usr/bin/env python3
"""s173_scan_refs.py — S173 phase 2: CORRECT-stride dex scan (OPS table from
s169_disasm). Find (1) all callers of Scope.getOrNull / Scope.get /
Scope.resolve, (2) const-string sites naming BaseCatalogFeatureFlagProvider,
(3) decode DecryptedFileProvider.<clinit> (18 units — the NDFE window)."""
import struct
import sys
import zipfile

sys.path.insert(0, '/home/z/my-project/scripts')
from s169_disasm import OPS, disasm
from cont9_dexdump import Dex

APK = '/home/z/my-project/upload/net.thunderbird.android_33.apk'
SCOPE = 'Lorg/koin/core/scope/Scope;'
WANT_CALLS = {'getOrNull', 'get', 'resolve', 'resolveFromContext'}
NEEDLES = ['BaseCatalogFeatureFlagProvider', 'No definition found']


def iter_methods(d):
    for i in range(d.class_defs_size):
        cdef = d.class_defs_off + i * 32
        try:
            cls = d.type_str(d.u(cdef, 4))
            info = d.class_methods(cdef)
        except Exception:
            continue
        for kind in ('direct', 'virtual'):
            for (mn, md, acc, sz, code) in info[kind]:
                yield cls, kind, mn, md, sz, code


def scan(dexes):
    call_hits = []
    str_hits = []
    for (n, b, d) in dexes:
        for (cls, kind, mn, md, sz, code) in iter_methods(d):
            if code == 0:
                continue
            off = code + 16  # code_item BYTE offset; insns at +16
            pc = 0
            while pc < sz:
                o = off + pc * 2
                op = b[o]
                ent = OPS.get(op)
                if ent is None:
                    pc += 1
                    continue
                size, fmt, name = ent
                try:
                    if fmt in ('35c', '35mi', '35ms', '45cc'):
                        idx = struct.unpack_from('<H', b, o + 2)[0]
                        rc, rmn, rmd = d.method_ref(idx)
                        if rc == SCOPE and rmn in WANT_CALLS:
                            call_hits.append((n, cls, mn, pc, rc, rmn, rmd))
                    elif fmt in ('3rc', '3rmi', '3rms', '5rc'):
                        idx = struct.unpack_from('<H', b, o + 2)[0]
                        rc, rmn, rmd = d.method_ref(idx)
                        if rc == SCOPE and rmn in WANT_CALLS:
                            call_hits.append((n, cls, mn, pc, rc, rmn, rmd))
                    elif op == 0x1a:
                        idx = struct.unpack_from('<H', b, o + 2)[0]
                        s = d.string(idx)
                        if any(x in s for x in NEEDLES):
                            str_hits.append((n, cls, mn, pc, s[:120]))
                    elif op == 0x1b:
                        idx = struct.unpack_from('<I', b, o + 2)[0]
                        s = d.string(idx)
                        if any(x in s for x in NEEDLES):
                            str_hits.append((n, cls, mn, pc, s[:120]))
                except Exception:
                    pass
                pc += max(1, size // 2)
    return call_hits, str_hits


def main():
    z = zipfile.ZipFile(APK)
    dexes = []
    for n in sorted(x for x in z.namelist()
                    if x.startswith('classes') and x.endswith('.dex')):
        b = z.read(n)
        dexes.append((n, b, Dex(b)))
    print(f"loaded {len(dexes)} dex files")

    print("\n== callers of Scope.get/getOrNull/resolve/resolveFromContext ==")
    call_hits, str_hits = scan(dexes)
    byname = {}
    for (n, cls, mn, pc, rc, rmn, rmd) in call_hits:
        byname.setdefault(rmn, []).append((cls, mn, pc, rmd))
    for rmn in sorted(byname):
        rows = byname[rmn]
        print(f"\n-- Scope.{rmn}: {len(rows)} call sites")
        for (cls, mn, pc, rmd) in rows:
            print(f"   {cls};.{mn} pc=0x{pc:x} proto={rmd[:80]}")

    print("\n== const-string sites (needles) ==")
    for (n, cls, mn, pc, s) in str_hits[:20]:
        print(f"   {cls};.{mn} pc=0x{pc:x} :: {s}")

    print("\n== DecryptedFileProvider.<clinit> decode ==")
    for (n, b, d) in dexes:
        cdef = d.find_class(
            'Lcom/fsck/k9/provider/DecryptedFileProvider;')
        if cdef is None:
            continue
        info = d.class_methods(cdef)
        for kind in ('direct', 'virtual'):
            for (mn, md, acc, sz, code) in info[kind]:
                print(f"-- {kind} {mn}{md} acc=0x{acc:x} units={sz}")
                if mn == '<clinit>':
                    disasm(d, b,
                           'Lcom/fsck/k9/provider/DecryptedFileProvider;',
                           mn, md)
        break
    print("done")


if __name__ == '__main__':
    main()
