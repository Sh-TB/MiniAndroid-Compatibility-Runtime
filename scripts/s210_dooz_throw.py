#!/usr/bin/env python3
"""S210 — dooz first-divergence forensics on Main (no W21 patch).

Questions this script answers from the SHA-pinned dooz APK:
  Q1. What IS the exception class `La;`? (superclass chain -> semantic)
  Q2. Which methods construct AND throw `La;`? (throw sites)
  Q3. Does ANY method in the whole app invoke `Lkc;.<init>`?
      (W21 chain says NO -> raw allocation -> zombie. Prove on Main's APK.)
  Q4. Disassemble the unwind chain frames: Lzs;.m, Lte1;.f, Lse1;.s,
      Lg;.q, Lg;.h, Lat;.a (call order + exception paths).
  Q5. Dump Lm7;.j (the W21-flagged RAW allocator).

Output: evidence/s210/dooz_throw_forensics.json + readable stdout.
"""
import json, struct, sys, zipfile
from pathlib import Path

APK = Path('/home/z/my-project/evidence/s207/runs/store_s208_dooz_ng2/data/app/io.github.yamin8000.dooz/base.apk')
OUT = Path('/home/z/my-project/evidence/s210')
OUT.mkdir(parents=True, exist_ok=True)

# ---- standard Dalvik opcode formats (AOSP dalvik opcode list) ----
# name -> (mnemonic, format) ; format determines size in 16-bit code units
FMT = {
    0x00: ('nop', '10x'), 0x01: ('move', '12x'), 0x02: ('move/from16', '22x'),
    0x03: ('move/16', '32x'), 0x04: ('move-wide', '12x'), 0x05: ('move-wide/from16', '22x'),
    0x06: ('move-wide/16', '32x'), 0x07: ('move-object', '12x'), 0x08: ('move-object/from16', '22x'),
    0x09: ('move-object/16', '32x'), 0x0a: ('move-result', '11x'), 0x0b: ('move-result-wide', '11x'),
    0x0c: ('move-result-object', '11x'), 0x0d: ('move-exception', '11x'),
    0x0e: ('return-void', '10x'), 0x0f: ('return', '11x'), 0x10: ('return-wide', '11x'),
    0x11: ('return-object', '11x'), 0x12: ('const/4', '11n'), 0x13: ('const/16', '21s'),
    0x14: ('const', '31i'), 0x15: ('const/high16', '21h'), 0x16: ('const-wide/16', '21s'),
    0x17: ('const-wide/32', '31i'), 0x18: ('const-wide', '51l'), 0x19: ('const-wide/high16', '21h'),
    0x1a: ('const-string', '21c'), 0x1b: ('const-string/jumbo', '31c'),
    0x1c: ('const-class', '21c'), 0x1d: ('monitor-enter', '11x'), 0x1e: ('monitor-exit', '11x'),
    0x1f: ('check-cast', '21c'), 0x20: ('instance-of', '22c'), 0x21: ('array-length', '12x'),
    0x22: ('new-instance', '21c'), 0x23: ('new-array', '22c'), 0x24: ('filled-new-array', '35c'),
    0x25: ('filled-new-array/range', '3rc'), 0x26: ('fill-array-data', '31t'),
    0x27: ('throw', '11x'), 0x28: ('goto', '10t'), 0x29: ('goto/16', '20t'),
    0x2a: ('goto/32', '30t'), 0x2b: ('packed-switch', '31t'), 0x2c: ('sparse-switch', '31t'),
    0x2d: ('cmpl-float', '23x'), 0x2e: ('cmpg-float', '23x'), 0x2f: ('cmpl-double', '23x'),
    0x30: ('cmpg-double', '23x'), 0x31: ('cmp-long', '23x'),
    0x32: ('if-eq', '22t'), 0x33: ('if-ne', '22t'), 0x34: ('if-lt', '22t'),
    0x35: ('if-ge', '22t'), 0x36: ('if-gt', '22t'), 0x37: ('if-le', '22t'),
    0x38: ('if-eqz', '21t'), 0x39: ('if-nez', '21t'), 0x3a: ('if-ltz', '21t'),
    0x3b: ('if-gez', '21t'), 0x3c: ('if-gtz', '21t'), 0x3d: ('if-lez', '21t'),
    0x44: ('aget', '23x'), 0x45: ('aget-wide', '23x'), 0x46: ('aget-object', '23x'),
    0x47: ('aget-boolean', '23x'), 0x48: ('aget-byte', '23x'), 0x49: ('aget-char', '23x'),
    0x4a: ('aget-short', '23x'), 0x4b: ('aput', '23x'), 0x4c: ('aput-wide', '23x'),
    0x4d: ('aput-object', '23x'), 0x4e: ('aput-boolean', '23x'), 0x4f: ('aput-byte', '23x'),
    0x50: ('aput-char', '23x'), 0x51: ('aput-short', '23x'),
    0x52: ('iget', '22c'), 0x53: ('iget-wide', '22c'), 0x54: ('iget-object', '22c'),
    0x55: ('iget-boolean', '22c'), 0x56: ('iget-byte', '22c'), 0x57: ('iget-char', '22c'),
    0x58: ('iget-short', '22c'), 0x59: ('iput', '22c'), 0x5a: ('iput-wide', '22c'),
    0x5b: ('iput-object', '22c'), 0x5c: ('iput-boolean', '22c'), 0x5d: ('iput-byte', '22c'),
    0x5e: ('iput-short', '22c'), 0x5f: ('iput-char', '22c'),
    0x60: ('sget', '21c'), 0x61: ('sget-wide', '21c'), 0x62: ('sget-object', '21c'),
    0x63: ('sget-boolean', '21c'), 0x64: ('sget-byte', '21c'), 0x65: ('sget-char', '21c'),
    0x66: ('sget-short', '21c'), 0x67: ('sput', '21c'), 0x68: ('sput-wide', '21c'),
    0x69: ('sput-object', '21c'), 0x6a: ('sput-boolean', '21c'), 0x6b: ('sput-byte', '21c'),
    0x6c: ('sput-char', '21c'), 0x6d: ('sput-short', '21c'),
    0x6e: ('invoke-virtual', '35c'), 0x6f: ('invoke-super', '35c'),
    0x70: ('invoke-direct', '35c'), 0x71: ('invoke-static', '35c'),
    0x72: ('invoke-interface', '35c'),
    0x74: ('invoke-virtual/range', '3rc'), 0x75: ('invoke-super/range', '3rc'),
    0x76: ('invoke-direct/range', '3rc'), 0x77: ('invoke-static/range', '3rc'),
    0x78: ('invoke-interface/range', '3rc'),
    0x7b: ('neg-int', '12x'), 0x7c: ('not-int', '12x'), 0x7d: ('neg-long', '12x'),
    0x7e: ('not-long', '12x'), 0x7f: ('neg-float', '12x'), 0x80: ('neg-double', '12x'),
    0x81: ('int-to-long', '12x'), 0x82: ('int-to-float', '12x'), 0x83: ('int-to-double', '12x'),
    0x84: ('long-to-int', '12x'), 0x85: ('long-to-float', '12x'), 0x86: ('long-to-double', '12x'),
    0x87: ('float-to-int', '12x'), 0x88: ('float-to-long', '12x'), 0x89: ('float-to-double', '12x'),
    0x8a: ('double-to-int', '12x'), 0x8b: ('double-to-long', '12x'), 0x8c: ('double-to-float', '12x'),
    0x8d: ('int-to-byte', '12x'), 0x8e: ('int-to-char', '12x'), 0x8f: ('int-to-short', '12x'),
    0x90: ('add-int', '23x'), 0x91: ('sub-int', '23x'), 0x92: ('mul-int', '23x'),
    0x93: ('div-int', '23x'), 0x94: ('rem-int', '23x'), 0x95: ('and-int', '23x'),
    0x96: ('or-int', '23x'), 0x97: ('xor-int', '23x'), 0x98: ('shl-int', '23x'),
    0x99: ('shr-int', '23x'), 0x9a: ('ushr-int', '23x'),
    0x9b: ('add-long', '23x'), 0x9c: ('sub-long', '23x'), 0x9d: ('mul-long', '23x'),
    0x9e: ('div-long', '23x'), 0x9f: ('rem-long', '23x'), 0xa0: ('and-long', '23x'),
    0xa1: ('or-long', '23x'), 0xa2: ('xor-long', '23x'), 0xa3: ('shl-long', '23x'),
    0xa4: ('shr-long', '23x'), 0xa5: ('ushr-long', '23x'),
    0xa6: ('add-float', '23x'), 0xa7: ('sub-float', '23x'), 0xa8: ('mul-float', '23x'),
    0xa9: ('div-float', '23x'), 0xaa: ('rem-float', '23x'),
    0xab: ('add-double', '23x'), 0xac: ('sub-double', '23x'), 0xad: ('mul-double', '23x'),
    0xae: ('div-double', '23x'), 0xaf: ('rem-double', '23x'),
    0xb0: ('add-int/2addr', '12x'), 0xb1: ('sub-int/2addr', '12x'), 0xb2: ('mul-int/2addr', '12x'),
    0xb3: ('div-int/2addr', '12x'), 0xb4: ('rem-int/2addr', '12x'), 0xb5: ('and-int/2addr', '12x'),
    0xb6: ('or-int/2addr', '12x'), 0xb7: ('xor-int/2addr', '12x'), 0xb8: ('shl-int/2addr', '12x'),
    0xb9: ('shr-int/2addr', '12x'), 0xba: ('ushr-int/2addr', '12x'),
    0xbb: ('add-long/2addr', '12x'), 0xbc: ('sub-long/2addr', '12x'), 0xbd: ('mul-long/2addr', '12x'),
    0xbe: ('div-long/2addr', '12x'), 0xbf: ('rem-long/2addr', '12x'), 0xc0: ('and-long/2addr', '12x'),
    0xc1: ('or-long/2addr', '12x'), 0xc2: ('xor-long/2addr', '12x'), 0xc3: ('shl-long/2addr', '12x'),
    0xc4: ('shr-long/2addr', '12x'), 0xc5: ('ushr-long/2addr', '12x'),
    0xc6: ('add-float/2addr', '12x'), 0xc7: ('sub-float/2addr', '12x'), 0xc8: ('mul-float/2addr', '12x'),
    0xc9: ('div-float/2addr', '12x'), 0xca: ('rem-float/2addr', '12x'),
    0xcb: ('add-double/2addr', '12x'), 0xcc: ('sub-double/2addr', '12x'), 0xcd: ('mul-double/2addr', '12x'),
    0xce: ('div-double/2addr', '12x'), 0xcf: ('rem-double/2addr', '12x'),
    0xd0: ('add-int/lit16', '22s'), 0xd1: ('rsub-int', '22s'),
    0xd2: ('mul-int/lit16', '22s'), 0xd3: ('div-int/lit16', '22s'), 0xd4: ('rem-int/lit16', '22s'),
    0xd5: ('and-int/lit16', '22s'), 0xd6: ('or-int/lit16', '22s'), 0xd7: ('xor-int/lit16', '22s'),
    0xd8: ('add-int/lit8', '22b'), 0xd9: ('rsub-int/lit8', '22b'), 0xda: ('mul-int/lit8', '22b'),
    0xdb: ('div-int/lit8', '22b'), 0xdc: ('rem-int/lit8', '22b'), 0xdd: ('and-int/lit8', '22b'),
    0xde: ('or-int/lit8', '22b'), 0xdf: ('xor-int/lit8', '22b'), 0xe0: ('shl-int/lit8', '22b'),
    0xe1: ('shr-int/lit8', '22b'), 0xe2: ('ushr-int/lit8', '22b'),
}
F1 = {'10x', '12x', '11n', '11x'}
F2 = {'20t', '21c', '21s', '21h', '21t', '22b', '22c', '22s', '22t', '22x', '23x'}
F3 = {'30t', '31c', '31i', '31t', '32x', '35c', '3rc'}
F5 = {'45cc', '4rcc', '51l'}

def fmt_size(fmt):
    if fmt in F1: return 1
    if fmt in F2: return 2
    if fmt in F3: return 3
    if fmt in F5: return 5
    return 1  # 10x/unknown fallback

def payload_size(u, units, i):
    ident = (u >> 8) & 0xff
    if ident == 0x01:  # packed-switch-payload
        width = units[i + 1] if i + 1 < len(units) else 0
        return width * 2 + 4
    if ident == 0x02:  # sparse-switch-payload
        n = units[i + 1] if i + 1 < len(units) else 0
        return n * 4 + 2
    if ident == 0x03:  # fill-array-data-payload
        ew = units[i + 1] if i + 1 < len(units) else 0
        lo = units[i + 2] if i + 2 < len(units) else 0
        hi = units[i + 3] if i + 3 < len(units) else 0
        n = (hi << 16) | lo
        total = n * ((ew * 8 + 7) // 8)  # bytes
        return (total + 1) // 2 + 4
    return 1

def uleb(buf, pos):
    result = shift = 0
    while True:
        b = buf[pos]; pos += 1
        result |= (b & 0x7f) << shift
        shift += 7
        if not (b & 0x80):
            return result, pos

def parse_dex(name, data, index):
    """Parse one dex file into index: {cls: {'super':..., 'methods': {(name,proto):(code_off, insns_units)}}}"""
    sids_size, sids_off = struct.unpack_from('<II', data, 0x38)
    tids_size, tids_off = struct.unpack_from('<II', data, 0x40)
    pids_size, pids_off = struct.unpack_from('<II', data, 0x48)
    fids_size, fids_off = struct.unpack_from('<II', data, 0x50)
    mids_size, mids_off = struct.unpack_from('<II', data, 0x58)
    cds_size, cds_off = struct.unpack_from('<II', data, 0x60)

    def gs(idx):
        off = struct.unpack_from('<I', data, sids_off + idx * 4)[0]
        n, p = uleb(data, off)
        return data[p: p + n].decode('utf-8', 'replace')

    def gt(idx):
        return gs(struct.unpack_from('<I', data, tids_off + idx * 4)[0])

    def proto_str(pidx):
        poff = pids_off + pidx * 12
        ret = gt(struct.unpack_from('<I', data, poff + 4)[0])
        po = struct.unpack_from('<I', data, poff + 8)[0]
        ps = ''
        if po:
            cnt = struct.unpack_from('<I', data, po)[0]
            for k in range(cnt):
                ps += gt(struct.unpack_from('<H', data, po + 4 + k * 2)[0])
        return ps + ')' + ret

    for ci in range(cds_size):
        off = cds_off + ci * 32
        class_idx, access, superclass, interfaces, src, anno, cdo, svals = struct.unpack_from('<8I', data, off)
        cls = gt(class_idx)
        sup = gt(superclass) if superclass != 0xFFFFFFFF else None
        ent = index.setdefault(cls, {'dex': name, 'super': sup, 'methods': {}})
        if sup and ent['super'] is None:
            ent['super'] = sup
        if cdo == 0:
            continue
        pos = cdo
        sf, pos = uleb(data, pos); inf, pos = uleb(data, pos)
        dm, pos = uleb(data, pos); vm, pos = uleb(data, pos)
        # DEX law: the *_idx_diff counter RESTARTS per section
        # (static_fields, instance_fields, direct_methods, virtual_methods are
        # four independent sorted lists; R8 keeps a class's members contiguous).
        fidx = 0
        for _ in range(sf):
            d, pos = uleb(data, pos); fidx += d; _, pos = uleb(data, pos)
        iidx = 0
        for _ in range(inf):
            d, pos = uleb(data, pos); iidx += d; _, pos = uleb(data, pos)
        midx = 0
        for _ in range(dm):
            d, pos = uleb(data, pos); midx += d; acc, pos = uleb(data, pos); code_off, pos = uleb(data, pos)
            mcls, mproto, mname = struct.unpack_from('<HHI', data, mids_off + midx * 8)
            nm = gs(mname)
            if code_off == 0:
                ent['methods'][(nm, 'ABSTRACT')] = None
                continue
            regs, ins, outs, tries, dbg, insns_n = struct.unpack_from('<HHHHII', data, code_off)
            units = list(struct.unpack_from(f'<{insns_n}H', data, code_off + 16)) if insns_n else []
            ent['methods'][(nm, proto_str(mproto))] = (code_off, units)
        midx = 0  # DEX law: idx_diff counter RESTARTS per section (virtual_methods is its own sorted list)
        for _ in range(vm):
            d, pos = uleb(data, pos); midx += d; acc, pos = uleb(data, pos); code_off, pos = uleb(data, pos)
            mcls, mproto, mname = struct.unpack_from('<HHI', data, mids_off + midx * 8)
            nm = gs(mname)
            if code_off == 0:
                ent['methods'][(nm, 'ABSTRACT')] = None
                continue
            regs, ins, outs, tries, dbg, insns_n = struct.unpack_from('<HHHHII', data, code_off)
            units = list(struct.unpack_from(f'<{insns_n}H', data, code_off + 16)) if insns_n else []
            ent['methods'][(nm, proto_str(mproto))] = (code_off, units)

def decode(index, cls, key):
    """Decode a method to a listing. Returns list of (pc, mnemonic, detail)."""
    ent = index.get(cls)
    if not ent: return None
    code_off, units = ent['methods'].get(key, (None, None))
    if units is None: return None
    out = []
    i = 0
    n = len(units)
    while i < n:
        u = units[i]
        op = u & 0xff
        mn, fmt = FMT.get(op, (f'op-{op:02x}', 'unk'))
        size = fmt_size(fmt)
        if op == 0x00 and (u >> 8) != 0:
            size = payload_size(u, units, i)
            mn = f'payload-{(u>>8)&0xff:02x}'
        detail = ''
        if fmt in ('21c', '31c') and i + 1 < n:
            idx = units[i + 1]
            if op == 0x1a: detail = f' string@{idx}'
            elif op in (0x1c, 0x1f, 0x22): detail = f' type@{idx}'
            elif op in range(0x60, 0x6d): detail = f' field@{idx}'
            elif op in range(0x6e, 0x73): detail = f' method@{idx}'
        elif fmt in ('22c',):
            if i + 1 < n:
                detail = f' field@{units[i+1]}'
        elif fmt in ('35c',) and i + 1 < n:
            detail = f' method@{units[i+1]}'
        elif fmt in ('3rc',) and i + 1 < n:
            detail = f' method@{units[i+1]}'
        elif op == 0x27:
            detail = ' ; throw'
        out.append((i, mn, detail.strip()))
        i += size
    return out

def resolve_type(index, idx_unused, txt):
    return txt

def main():
    index = {}
    with zipfile.ZipFile(APK) as z:
        for nm in z.namelist():
            if nm.startswith('classes') and nm.endswith('.dex'):
                parse_dex(nm, z.read(nm), index)
    print(f'classes parsed: {len(index)}')
    report = {'apk': str(APK), 'classes': len(index)}

    # Q1: what is La; ?
    la = index.get('La;')
    if la:
        chain = ['La;']
        sup = la['super']
        while sup and sup in index:
            chain.append(sup)
            sup = index[sup]['super']
        if sup: chain.append(sup + ' (external)')
        report['La;_extends_chain'] = chain
        print('Q1: La; extends chain:', ' -> '.join(chain))
        la_methods = list(la['methods'].keys())
        report['La;_methods'] = [f'{n}{p}' for n, p in la_methods]
        print(f'Q1: La; methods ({len(la_methods)}):', [f'{n}' for n, _ in la_methods][:15])
    else:
        print('Q1: La; NOT FOUND in app DEX (framework class?)')

    # Q2: throw sites of La; — precise pass below (with type resolution)
    type_res = {}  # (dex, type_idx) -> desc
    with zipfile.ZipFile(APK) as z:
        for nm in z.namelist():
            if not (nm.startswith('classes') and nm.endswith('.dex')): continue
            data = z.read(nm)
            sids_size, sids_off = struct.unpack_from('<II', data, 0x38)
            tids_size, tids_off = struct.unpack_from('<II', data, 0x40)
            def gs2(idx):
                off = struct.unpack_from('<I', data, sids_off + idx * 4)[0]
                n, p = uleb(data, off)
                return data[p: p + n].decode('utf-8', 'replace')
            for t in range(tids_size):
                si = struct.unpack_from('<I', data, tids_off + t * 4)[0]
                type_res[(nm, t)] = gs2(si)
    report['type_resolved'] = len(type_res)

    la_thowers = []
    for cls, ent in index.items():
        for (nm, proto), code in ent['methods'].items():
            if code is None: continue
            _, units = code
            i = 0; n = len(units)
            new_la = False; has_throw = False
            while i < n:
                u = units[i]; op = u & 0xff
                mn, fmt = FMT.get(op, ('?', 'unk'))
                size = fmt_size(fmt)
                if op == 0x00 and (u >> 8) != 0: size = payload_size(u, units, i)
                if op == 0x22 and i + 1 < n:
                    td = type_res.get((ent['dex'], units[i + 1]), '')
                    if td == 'La;': new_la = True
                if op == 0x27: has_throw = True
                i += size
            if new_la and has_throw:
                la_thowers.append(f'{cls}.{nm}{proto}')
    report['La;_construct_throw_sites'] = la_thowers
    print(f'Q2: methods constructing AND throwing La;: {len(la_thowers)}')
    for t in la_thowers[:10]:
        print('   ', t)

    # Q3: does ANY method invoke Lkc;.<init>?
    kc_inits = []
    for cls, ent in index.items():
        for (nm, proto), code in ent['methods'].items():
            if code is None: continue
            _, units = code
            i = 0; n = len(units)
            while i < n:
                u = units[i]; op = u & 0xff
                mn, fmt = FMT.get(op, ('?', 'unk'))
                size = fmt_size(fmt)
                if op == 0x00 and (u >> 8) != 0: size = payload_size(u, units, i)
                if fmt == '35c' and i + 1 < n:
                    midx = units[i + 1]
                    # need method resolution: parse method_ids lazily
                    pass
                i += size
    # method resolution per dex
    meth_res = {}
    with zipfile.ZipFile(APK) as z:
        for nm in z.namelist():
            if not (nm.startswith('classes') and nm.endswith('.dex')): continue
            data = z.read(nm)
            sids_size, sids_off = struct.unpack_from('<II', data, 0x38)
            tids_size, tids_off = struct.unpack_from('<II', data, 0x40)
            mids_size, mids_off = struct.unpack_from('<II', data, 0x58)
            def gs3(idx):
                off = struct.unpack_from('<I', data, sids_off + idx * 4)[0]
                n, p = uleb(data, off)
                return data[p: p + n].decode('utf-8', 'replace')
            def gt3(idx):
                return gs3(struct.unpack_from('<I', data, tids_off + idx * 4)[0])
            for m in range(mids_size):
                mcls, mproto, mname = struct.unpack_from('<HHI', data, mids_off + m * 8)
                meth_res[(nm, m)] = (gt3(mcls), gs3(mname))
    report['methods_resolved'] = len(meth_res)

    kc_ctor_callers = []
    for cls, ent in index.items():
        for (nm, proto), code in ent['methods'].items():
            if code is None: continue
            _, units = code
            i = 0; n = len(units)
            while i < n:
                u = units[i]; op = u & 0xff
                mn, fmt = FMT.get(op, ('?', 'unk'))
                size = fmt_size(fmt)
                if op == 0x00 and (u >> 8) != 0: size = payload_size(u, units, i)
                if op == 0x70 and i + 1 < n:  # invoke-direct
                    mc, mn2 = meth_res.get((ent['dex'], units[i + 1]), ('', ''))
                    if mc == 'Lkc;' and mn2 == '<init>':
                        kc_ctor_callers.append(f'{cls}.{nm}{proto}')
                i += size
    report['Lkc_ctor_invoke_sites'] = kc_ctor_callers
    print(f'Q3: invoke-direct Lkc;.<init> sites: {len(kc_ctor_callers)}')
    for t in kc_ctor_callers[:10]:
        print('   ', t)

    # also: new-instance Lkc; sites (raw allocations)
    kc_news = []
    for cls, ent in index.items():
        for (nm, proto), code in ent['methods'].items():
            if code is None: continue
            _, units = code
            i = 0; n = len(units)
            while i < n:
                u = units[i]; op = u & 0xff
                mn, fmt = FMT.get(op, ('?', 'unk'))
                size = fmt_size(fmt)
                if op == 0x00 and (u >> 8) != 0: size = payload_size(u, units, i)
                if op == 0x22 and i + 1 < n:
                    td = type_res.get((ent['dex'], units[i + 1]), '')
                    if td == 'Lkc;':
                        kc_news.append(f'{cls}.{nm}{proto}')
                i += size
    report['Lkc_new_instance_sites'] = kc_news
    print(f'Q3b: new-instance Lkc; sites: {len(kc_news)}')
    for t in kc_news[:10]:
        print('   ', t)

    # Q4: unwind chain methods
    chain = [('Lzs;', 'm'), ('Lte1;', 'f'), ('Lse1;', 's'), ('Lg;', 'q'), ('Lg;', 'h'), ('Lat;', 'a')]
    report['unwind_chain'] = {}
    for cls, mname in chain:
        ent = index.get(cls)
        if not ent:
            report['unwind_chain'][f'{cls}.{mname}'] = 'CLASS NOT FOUND'
            continue
        matches = [k for k in ent['methods'] if k[0] == mname]
        for key in matches:
            lst = decode(index, cls, key)
            if lst is None: continue
            kdesc = f'{cls}.{mname}{key[1]}'
            txt = [f'{pc:04d}: {mn} {dt}'.rstrip() for pc, mn, dt in lst]
            report['unwind_chain'][kdesc] = txt
            print(f'--- {kdesc} ({len(txt)} units) first 25:')
            for line in txt[:25]:
                print('   ', line)
            print()

    # Q5: Lm7;.j
    ent = index.get('Lm7;')
    if ent:
        for key in [k for k in ent['methods'] if k[0] == 'j']:
            lst = decode(index, 'Lm7;', key)
            kdesc = f'Lm7;.j{key[1]}'
            txt = [f'{pc:04d}: {mn} {dt}'.rstrip() for pc, mn, dt in lst]
            report[f'dump_{kdesc}'] = txt
            print(f'--- {kdesc} ({len(txt)} units) FULL:')
            for line in txt:
                print('   ', line)
            print()

    (OUT / 'dooz_throw_forensics.json').write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print('saved', OUT / 'dooz_throw_forensics.json')

if __name__ == '__main__':
    main()
