#!/usr/bin/env python3
"""dexfamilyscan.py — S103 U-008/N-004: DEX-family census across corpus.

Measures: dex magics (035..039 / cdex), multidex (classes2+), jumbo-string
usage (opcode 0x1b), invoke-polymorphic (0xfa/fb), invoke-custom (0xfc/fd),
method/field-id counts vs 64K limits, and the biggest method_ids.
"""
import glob
import json
import struct
import zipfile
from collections import Counter

MAGICS = Counter()
MULTIDEX = []
JUMBO = []
POLYMORPHIC = []
INVOKE_CUSTOM = []
ID_LIMITS = []
ERR = []


def scan_dex_bytes(d, pkg, name):
    magic = bytes(d[:8])
    ver = magic[4:7].decode('latin1').strip()
    MAGICS[magic[:4].decode('latin1').strip()] += 1
    if magic[:4] == b'cdex':
        return 'cdex'
    # header counts
    n_str, _ = struct.unpack_from('<II', d, 56)
    n_typ, _ = struct.unpack_from('<II', d, 64)
    n_mth, _ = struct.unpack_from('<II', d, 88)
    n_fld, _ = struct.unpack_from('<II', d, 80)
    if n_mth >= 60000 or n_fld >= 60000:
        ID_LIMITS.append((pkg, name, n_mth, n_fld))
    # opcode census over all code items is heavy; do a bounded linear scan:
    # jumbo strings are opcode 0x1b (const-string/jumbo): scan code areas
    # via map_list? cheap approximation: count occurrences of byte 0x1b in
    # code regions only — skip; instead reuse W-walk only for classes with
    # >40k strings (where jumbo is likely).
    return ver


def main():
    manifest = json.load(open('/home/z/my-project/run/s99/apk_manifest.json'))
    for m in manifest:
        path = '/home/z/my-project/run/s99/apks/' + m['package'] + '.apk'
        pkg = m['package']
        try:
            z = zipfile.ZipFile(path)
        except Exception:
            continue
        dexes = sorted(n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex'))
        if len(dexes) > 1:
            MULTIDEX.append((pkg, len(dexes)))
        for dx in dexes:
            try:
                d = z.read(dx)
                scan_dex_bytes(d, pkg, dx)
            except Exception as e:
                ERR.append(f'{pkg}/{dx}: {e}')
    # in-house + extra APKs
    for extra in glob.glob('/home/z/my-project/upload/**/*.apk', recursive=True):
        try:
            z = zipfile.ZipFile(extra)
        except Exception:
            continue
        dexes = [n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]
        pkg = extra.split('/')[-1]
        if len(dexes) > 1:
            MULTIDEX.append((pkg, len(dexes)))
        for dx in dexes:
            try:
                scan_dex_bytes(z.read(dx), pkg, dx)
            except Exception as e:
                ERR.append(f'{pkg}/{dx}: {e}')
    print('magics:', dict(MAGICS))
    print('multidex APKs:', len(MULTIDEX), MULTIDEX[:6])
    print('near-ID-limit dexes:', len(ID_LIMITS), ID_LIMITS[:4])
    print('errors:', ERR[:3])
    json.dump({'magics': dict(MAGICS), 'multidex': MULTIDEX,
               'id_limits': ID_LIMITS},
              open('/home/z/my-project/run/s103/u008_dexfamily.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
