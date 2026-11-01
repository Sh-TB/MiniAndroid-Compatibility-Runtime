#!/usr/bin/env python3
"""s143_yk0_sput.py — find every sput-object site writing yk0.Instance
across the forkgram dexes, with the enclosing method, so the
instance-assignment law (who must run before needShowPasscode) is pinned.

Two-phase: phase A scans code_words for the 22c sput-object opcode with
the target field index (word2 == fidx); phase B maps the hit offset to the
enclosing method via class_data code_off ranges (no string decode in the
hot loop).
"""
import sys, zipfile, importlib.util, struct

spec = importlib.util.spec_from_file_location(
    'cd', '/home/z/my-project/scripts/cont9_dexdump.py')
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)

APK = '/home/z/my-project/upload/tg/forkgram.apk'
CLS = 'Lorg/telegram/ui/Components/yk0;'

z = zipfile.ZipFile(APK)
for dn in ['classes.dex', 'classes2.dex', 'classes3.dex',
           'classes4.dex', 'classes5.dex']:
    d = cd.Dex(z.read(dn))
    fidx = None
    for i in range(d.field_ids_size):
        c, f, t = d.field_ref(i)
        if c == CLS and f == 'Instance':
            fidx = i
            break
    if fidx is None:
        continue
    print(f'{dn}: yk0.Instance field_id={fidx}')
    # class def -> code offsets + method names
    coff = d.find_class(CLS)
    if coff is None:
        continue
    # scan every class's methods for the sput pattern is heavy; instead
    # scan the whole dex insns region for 22c with field == fidx.
    b = d.b
    field_ids_off = d.field_ids_off
    # gather all (code_off, mname) for the yk0 class
    cm = d.class_methods(coff)
    print('  yk0 methods:', [(m[0], m[3]) for m in cm['direct'] + cm['virtual']])
    # search sput-object 0x6f in each method body
    for kind in ('direct', 'virtual'):
        for mname, mdesc, acc, sz, code in cm[kind]:
            if not code:
                continue
            insns_size = d.u(code + 12, 4)
            wo = code + 16
            for w in range(insns_size):
                word = d.u(wo + w * 2, 2)
                if (word & 0xff) == 0x6f:  # sput-object 22c
                    if (w + 1 < insns_size
                            and d.u(wo + (w + 1) * 2, 2) == fidx):
                        print(f'  HIT sput-object yk0.Instance in .{mname}'
                              f'{mdesc} at word {w} (byte_pc={w*2:#x})')
