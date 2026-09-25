#!/usr/bin/env python3
"""dex_typescan.py — S103 MAXIMUM-EXTRACTION N-001 collision-corpus scanner.

Walks every class/method code item in every dex of every corpus APK and
records ALL `instance-of` (0x20), `check-cast` (0x1f) and `const-class`
(0x1c) type operands, resolved to real descriptors.

Purpose: measure whether any corpus APK's own bytecode executes type tests
against the androidx/material classes that MiniAndroid's inflater maps AWAY
to platform classes (AppCompatTextView->TextView, FloatingActionButton->
ImageView, ...) — the same identity-law family as the S101 Toolbar law.

Output: JSON {apk: {instanceof: {desc: count}, checkcast: {...}, constclass: {...}}}
"""
import json
import struct
import sys
import zipfile
from collections import defaultdict

# opcode -> width in 16-bit code units (standard dalvik)
W = {}
for i in range(0x100):
    W[i] = 1  # default; corrected below
_W = {
    0x00: 1, 0x01: 1, 0x02: 2, 0x03: 3, 0x04: 1, 0x05: 2, 0x06: 3, 0x07: 1,
    0x08: 2, 0x09: 3, 0x0a: 1, 0x0b: 1, 0x0c: 1, 0x0d: 1, 0x0e: 1, 0x0f: 1,
    0x10: 1, 0x11: 1, 0x12: 1, 0x13: 2, 0x14: 3, 0x15: 2, 0x16: 2, 0x17: 3,
    0x18: 5, 0x19: 2, 0x1a: 2, 0x1b: 3, 0x1c: 2, 0x1d: 1, 0x1e: 1, 0x1f: 2,
    0x20: 2, 0x21: 1, 0x22: 2, 0x23: 2, 0x24: 3, 0x25: 3, 0x26: 3, 0x27: 1,
    0x28: 1, 0x29: 2, 0x2a: 3, 0x2b: 3, 0x2c: 3, 0x2d: 2, 0x2e: 2, 0x2f: 2,
    0x30: 2, 0x31: 2, 0x32: 2, 0x33: 2, 0x34: 2, 0x35: 2, 0x36: 2, 0x37: 2,
    0x38: 2, 0x39: 2, 0x3a: 2, 0x3b: 2, 0x3c: 2, 0x3d: 2,
    0x44: 2, 0x45: 2, 0x46: 2, 0x47: 2, 0x48: 2, 0x49: 2, 0x4a: 2, 0x4b: 2,
    0x4c: 2, 0x4d: 2, 0x4e: 2, 0x4f: 2, 0x50: 2, 0x51: 2,
    0x52: 2, 0x53: 2, 0x54: 2, 0x55: 2, 0x56: 2, 0x57: 2, 0x58: 2, 0x59: 2,
    0x5a: 2, 0x5b: 2, 0x5c: 2, 0x5d: 2, 0x5e: 2, 0x5f: 2,
    0x60: 2, 0x61: 2, 0x62: 2, 0x63: 2, 0x64: 2, 0x65: 2, 0x66: 2, 0x67: 2,
    0x68: 2, 0x69: 2, 0x6a: 2, 0x6b: 2, 0x6c: 2, 0x6d: 2,
    0x6e: 3, 0x6f: 3, 0x70: 3, 0x71: 3, 0x72: 3, 0x74: 3, 0x75: 3, 0x76: 3,
    0x77: 3, 0x78: 3,
    0x7b: 1, 0x7c: 1, 0x7d: 1, 0x7e: 1, 0x7f: 1, 0x80: 1, 0x81: 1, 0x82: 1,
    0x83: 1, 0x84: 1, 0x85: 1, 0x86: 1, 0x87: 1, 0x88: 1, 0x89: 1, 0x8a: 1,
    0x8b: 1, 0x8c: 1, 0x8d: 1, 0x8e: 1, 0x8f: 1,
}
for i in range(0x90, 0xb0):
    _W[i] = 2          # binop 23x/22s
for i in range(0xb0, 0xd0):
    _W[i] = 1          # binop/2addr
for i in range(0xd0, 0xd8):
    _W[i] = 2          # binop/lit16
for i in range(0xd8, 0xe3):
    _W[i] = 2          # binop/lit8
_W[0xfa] = 4          # invoke-polymorphic (45cc)
_W[0xfb] = 4          # invoke-polymorphic/range (4rcc)
_W[0xfc] = 3          # invoke-custom
_W[0xfd] = 3          # invoke-custom/range
for k, v in _W.items():
    W[k] = v


def uleb(buf, off):
    result = 0
    shift = 0
    while True:
        b = buf[off]
        off += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, off


def parse_strings(d):
    n, off = struct.unpack_from('<II', d, 56)
    strs = []
    for i in range(n):
        so = struct.unpack_from('<I', d, off + i * 4)[0]
        _, p = uleb(d, so)          # utf16 length (ignored; we read MUTF8)
        end = d.index(b'\x00', p)
        strs.append(d[p:end].decode('utf-8', errors='replace'))
    return strs


def parse_types(d, strs):
    n, off = struct.unpack_from('<II', d, 64)
    types = []
    for i in range(n):
        di = struct.unpack_from('<I', d, off + i * 4)[0]
        types.append(strs[di] if di < len(strs) else '<?>')
    return types


def parse_method_ids(d, strs, types):
    n, off = struct.unpack_from('<II', d, 88)
    methods = []
    for i in range(n):
        cls, proto, name = struct.unpack_from('<HHI', d, off + i * 8)
        cls_d = types[cls] if cls < len(types) else '<?>'
        methods.append(f'{cls_d}.{strs[name] if name < len(strs) else "?"}')
    return methods


def scan_code(d, insns_off, insns_size, types, out, site=''):
    """Walk one code item; record 21c type operands."""
    i = 0
    n = insns_size
    while i < n:
        try:
            # dalvik: opcode = LOW byte of the first 16-bit unit (LE memory order)
            opbyte = d[insns_off + i * 2]
        except IndexError:
            break
        if opbyte == 0x00 and i + 1 < n:
            # possible payload nop
            ident = struct.unpack_from('<H', d, insns_off + i * 2)[0]
            if ident == 0x0100:  # packed-switch payload
                size = struct.unpack_from('<H', d, insns_off + i * 2 + 2)[0]
                w = 4 + size * 2
                i += w
                continue
            if ident == 0x0200:  # sparse-switch payload
                size = struct.unpack_from('<H', d, insns_off + i * 2 + 2)[0]
                w = 2 + size * 4
                i += w
                continue
            if ident == 0x0300:  # fill-array-data payload
                ew, size = struct.unpack_from('<HI', d, insns_off + i * 2 + 2)
                total = 8 + size * ew
                w = (total + 1) // 2
                i += w
                continue
            i += 1
            continue
        w = W[opbyte] if opbyte < len(W) else 1
        if opbyte in (0x1f, 0x20, 0x1c) and i + 1 < n:
            tidx = struct.unpack_from('<H', d, insns_off + i * 2 + 2)[0]
            desc = types[tidx] if tidx < len(types) else '<?>'
            key = {0x1f: 'checkcast', 0x20: 'instanceof', 0x1c: 'constclass'}[opbyte]
            out[key][desc] += 1
            if site:
                out.setdefault('sites', defaultdict(set))
                out['sites'][f'{key} {desc}'].add(site)
        i += w


def scan_dex(d, class_filter=None):
    strs = parse_strings(d)
    types = parse_types(d, strs)
    method_ids = parse_method_ids(d, strs, types)
    cdefs_n, cdefs_off = struct.unpack_from('<II', d, 96)
    out = {'instanceof': defaultdict(int), 'checkcast': defaultdict(int),
           'constclass': defaultdict(int), 'classes': 0, 'sites': defaultdict(set)}
    for i in range(cdefs_n):
        base = cdefs_off + i * 32
        class_idx, access, sup, iface_off, src, anno, cdata_off, svals = \
            struct.unpack_from('<IIIIIIII', d, base)
        desc = types[class_idx] if class_idx < len(types) else '<?>'
        if class_filter and not class_filter(desc):
            continue
        out['classes'] += 1
        if cdata_off == 0:
            continue
        p = cdata_off
        sfields, ifields, dmethods, vmethods = uleb(d, p)[0], 0, 0, 0
        sfields, p = uleb(d, p)
        ifields, p = uleb(d, p)
        dmethods, p = uleb(d, p)
        vmethods, p = uleb(d, p)
        # encoded_field skip: static, instance
        for _ in range(sfields + ifields):
            _, p = uleb(d, p)
            _, p = uleb(d, p)
        midx = None
        for kind, count in (('direct', dmethods), ('virtual', vmethods)):
            if kind == 'virtual':
                midx = None  # each list's first element is represented directly
            for _ in range(count):
                diff, p = uleb(d, p)
                _, p = uleb(d, p)
                code_off, p = uleb(d, p)
                if midx is None:
                    midx = diff
                else:
                    midx += diff
                if code_off == 0 or midx >= len(method_ids):
                    continue
                mname = method_ids[midx]
                regs, ins, outs, tries, dbg, insns_size = struct.unpack_from(
                    '<HHHHII', d, code_off)
                if insns_size == 0:
                    continue
                scan_code(d, code_off + 16, insns_size, types, out, site=mname)
    return out


MAPPED_AWAY = [
    'Landroidx/appcompat/widget/AppCompatTextView;',
    'Landroidx/appcompat/widget/AppCompatButton;',
    'Landroidx/appcompat/widget/AppCompatEditText;',
    'Landroidx/appcompat/widget/AppCompatImageView;',
    'Landroidx/appcompat/widget/AppCompatCheckBox;',
    'Landroidx/appcompat/widget/AppCompatRadioButton;',
    'Landroidx/appcompat/widget/AppCompatSpinner;',
    'Lcom/google/android/material/button/MaterialButton;',
    'Lcom/google/android/material/textfield/MaterialAutoCompleteTextView;',
    'Lcom/google/android/material/textfield/TextInputEditText;',
    'Lcom/google/android/material/floatingactionbutton/FloatingActionButton;',
    'Landroidx/appcompat/widget/Toolbar;',
    'Landroid/widget/Toolbar;',
]


def main():
    manifest = json.load(open('/home/z/my-project/run/s99/apk_manifest.json'))
    apks = [('/home/z/my-project/run/s99/apks/' + m['package'] + '.apk',
             m['package']) for m in manifest]
    # in-house + extras used by the wave
    extra = {
        'de.georgsieber.ballbreak': '/home/z/my-project/run/s99/apks/de.georgsieber.ballbreak.apk',
    }
    result = {}
    for path, pkg in apks:
        try:
            z = zipfile.ZipFile(path)
        except Exception as e:
            result[pkg] = {'error': str(e)}
            continue
        dexes = [n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]
        agg = {'instanceof': defaultdict(int), 'checkcast': defaultdict(int),
               'constclass': defaultdict(int), 'dexes': len(dexes), 'classes': 0}
        for dx in dexes:
            try:
                r = scan_dex(z.read(dx))
            except Exception as e:
                agg.setdefault('dex_errors', []).append(f'{dx}: {e}')
                continue
            agg['classes'] += r['classes']
            for k in ('instanceof', 'checkcast', 'constclass'):
                for desc, c in r[k].items():
                    agg[k][desc] += c
            for k, ms in r.get('sites', {}).items():
                agg.setdefault('sites', defaultdict(set))[k] |= ms
        # reduce to interesting targets + totals
        ident_hits = {t: agg['instanceof'].get(t, 0) for t in MAPPED_AWAY
                      if agg['instanceof'].get(t, 0) > 0}
        cast_hits = {t: agg['checkcast'].get(t, 0) for t in MAPPED_AWAY
                     if agg['checkcast'].get(t, 0) > 0}
        sites = {}
        for k, ms in agg.get('sites', {}).items():
            if any(t in k for t in MAPPED_AWAY):
                sites[k] = sorted(ms)[:12]
        result[pkg] = {
            'dexes': agg['dexes'], 'classes_scanned': agg['classes'],
            'instanceof_total_ops': sum(agg['instanceof'].values()),
            'instanceof_unique_types': len(agg['instanceof']),
            'identity_hits_instanceof': ident_hits,
            'identity_hits_checkcast': cast_hits,
            'identity_sites': sites,
        }
    outp = '/home/z/my-project/run/s103/u001_typescan.json'
    json.dump(result, open(outp, 'w'), indent=1)
    # console summary
    n_ident = 0
    for pkg, r in sorted(result.items()):
        ih = r.get('identity_hits_instanceof', {})
        ch = r.get('identity_hits_checkcast', {})
        if ih or ch:
            n_ident += 1
            print(f'== {pkg} instanceof_total={r.get("instanceof_total_ops",0)}')
            for t, c in sorted(ih.items()):
                print(f'   instanceof {t} x{c}')
            for t, c in sorted(ch.items()):
                print(f'   checkcast  {t} x{c}')
    print(f'\nAPKs with identity hits: {n_ident} / {len(result)}')
    print('saved:', outp)


if __name__ == '__main__':
    main()
