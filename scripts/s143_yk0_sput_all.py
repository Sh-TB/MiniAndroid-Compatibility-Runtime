#!/usr/bin/env python3
"""s143_yk0_sput_all.py — ALL sput-object writers of yk0.Instance across
every class of every forkgram dex (index-gated two-phase, no string decode
in the hot loop). Also finds sget-object READERS so the read-before-write
window can be proven.
"""
import sys, zipfile, importlib.util

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
    print(f'== {dn}: field_id={fidx} ==', flush=True)
    hits = 0
    for ci in range(d.class_defs_size):
        off = d.class_defs_off + ci * 32
        cd_off = d.u(off + 24, 4)
        if not cd_off:
            continue
        cls_idx = d.u(off, 4)
        try:
            cm = d.class_methods(off)
        except Exception:
            continue
        for kind in ('direct', 'virtual'):
            for mname, mdesc, acc, sz, code in cm[kind]:
                if not code:
                    continue
                insns_size = d.u(code + 12, 4)
                wo = code + 16
                for w in range(insns_size):
                    word = d.u(wo + w * 2, 2)
                    op = word & 0xff
                    if op in (0x62, 0x67):  # sget-object / sput-object
                        if (w + 1 < insns_size
                                and d.u(wo + (w + 1) * 2, 2) == fidx):
                            clsname = d.type_str(cls_idx)
                            kindn = 'WRITE' if op == 0x6f else 'READ '
                            print(f'  {kindn} {clsname}.{mname}{mdesc}'
                                  f' word={w} byte_pc={w*2:#x}', flush=True)
                            hits += 1
    print(f'  ({hits} hits in {dn})', flush=True)
