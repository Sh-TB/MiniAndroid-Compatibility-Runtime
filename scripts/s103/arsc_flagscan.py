#!/usr/bin/env python3
"""arsc_flagscan.py — S103 U-007: measure OFFSET16/COMPACT/SPARSE usage in
every corpus APK's resources.arsc (and in-house fixtures).

AOSP law pinned from frameworks/base/libs/androidfw ResourceTypes.h:
  ResTable_type.flags: FLAG_SPARSE=0x01, FLAG_OFFSET16=0x02
  ResTable_entry.flags: FLAG_COMPACT=0x0008
  ResStringPool_header.flags: UTF8_FLAG=1<<8
"""
import glob
import json
import struct
import zipfile


def u16(b, o):
    return struct.unpack_from('<H', b, o)[0]


def u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def scan_arsc(data):
    """Walk table chunks; count type-chunk flags + entry flags + pool flags."""
    out = {'types': 0, 'sparse': 0, 'offset16': 0, 'compact_entries': 0,
           'complex_entries': 0, 'simple_entries': 0, 'pools_utf8': 0,
           'pool_flags': [], 'packages': 0, 'parse_ok': False}
    if len(data) < 12:
        out['error'] = 'too small'
        return out
    typ, hdr_sz, size = u16(data, 0), u16(data, 2), u32(data, 4)
    if typ != 0x0002:  # RES_TABLE_TYPE
        out['error'] = f'not a table (type=0x{typ:x})'
        return out
    package_count = u32(data, 8)
    off = hdr_sz
    end = min(size, len(data))
    while off + 8 <= end:
        ct, chs, csize = u16(data, off), u16(data, off + 2), u32(data, off + 4)
        if chs < 8 or off + csize > len(data):
            break
        if ct == 0x0001:  # RES_STRING_POOL_TYPE (global string pool)
            flags = u32(data, off + 8)
            out['pool_flags'].append(flags)
            if flags & 0x100:
                out['pools_utf8'] += 1
        elif ct == 0x0200:  # RES_TABLE_PACKAGE_TYPE
            out['packages'] += 1
            poff = off
            pend = off + csize
            po = poff + u16(data, poff + 2)
            # inside package: type string pool, key string pool, type specs, types
            while po + 8 <= pend:
                pt, phs, psz = u16(data, po), u16(data, po + 2), u32(data, po + 4)
                if psz < 8 or po + psz > len(data):
                    break
                if pt == 0x0202:  # RES_TABLE_TYPE_SPEC_TYPE: skip (header+mask data)
                    po += psz
                    continue
                if pt == 0x0001:
                    flags = u32(data, po + 8)
                    if flags & 0x100:
                        out['pools_utf8'] += 1
                if pt == 0x0201:  # RES_TABLE_TYPE_TYPE (a ResTable_type)
                    tflags = data[po + 10]
                    out['types'] += 1
                    if tflags & 0x01:
                        out['sparse'] += 1
                    if tflags & 0x02:
                        out['offset16'] += 1
                    # walk entries of this type chunk (approximate, bounded)
                    eid = data[po + 8]
                    tflags = data[po + 10]
                    entry_count = u32(data, po + 12)
                    entries_start = u32(data, po + 16)
                    hs = phs
                    if not (tflags & 0x01):
                        for i in range(entry_count):
                            eo = u32(data, po + hs + i * 4)
                            if eo == 0xFFFFFFFF:
                                continue
                            ep = po + entries_start + eo
                            if ep + 8 > len(data):
                                break
                            eflags = u16(data, ep + 2)
                            if eflags & 0x0008:
                                out['compact_entries'] += 1
                            elif eflags & 0x0001:
                                out['complex_entries'] += 1
                            else:
                                out['simple_entries'] += 1
                po += psz
        off += csize
    out['parse_ok'] = True
    return out


def main():
    manifest = json.load(open('/home/z/my-project/run/s99/apk_manifest.json'))
    paths = [('/home/z/my-project/run/s99/apks/' + m['package'] + '.apk',
              m['package']) for m in manifest]
    total = {'with_arsc': 0, 'offset16_apks': [], 'compact_apks': [],
             'sparse_apks': [], 'errors': []}
    for path, pkg in paths:
        try:
            z = zipfile.ZipFile(path)
            if 'resources.arsc' not in z.namelist():
                continue
            data = z.read('resources.arsc')
            r = scan_arsc(data)
            total['with_arsc'] += 1
            if not r.get('parse_ok'):
                total['errors'].append(f'{pkg}: {r.get("error")}')
                continue
            if r['offset16']:
                total['offset16_apks'].append((pkg, r['offset16']))
            if r['compact_entries']:
                total['compact_apks'].append((pkg, r['compact_entries']))
            if r['sparse']:
                total['sparse_apks'].append((pkg, r['sparse']))
        except Exception as e:
            total['errors'].append(f'{pkg}: {e}')
    json.dump(total, open('/home/z/my-project/run/s103/u007_arsc_scan.json', 'w'), indent=1)
    print('APKs with arsc:', total['with_arsc'])
    print('APKs using OFFSET16:', len(total['offset16_apks']), total['offset16_apks'][:6])
    print('APKs using COMPACT entries:', len(total['compact_apks']), total['compact_apks'][:6])
    print('APKs using SPARSE types:', len(total['sparse_apks']),
          [p for p, _ in total['sparse_apks']][:8])
    print('errors:', total['errors'][:5])


if __name__ == '__main__':
    main()
