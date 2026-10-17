#!/usr/bin/env python3
"""CONT-75 DEX dumper: sequential class_def walk (field/method idx_diff are
dex-wide running differences), methods of one class, bytecode window.

Usage: cont75_dex_dump.py <apk> <descriptor> [method_name] [pc] [before] [after]
"""
import sys, zipfile, struct

apk, desc = sys.argv[1], sys.argv[2]
mname = sys.argv[3] if len(sys.argv) > 3 else None
pc = int(sys.argv[4], 0) if len(sys.argv) > 4 else None
before = int(sys.argv[5]) if len(sys.argv) > 5 else 10
after = int(sys.argv[6]) if len(sys.argv) > 6 else 10

z = zipfile.ZipFile(apk)
dex = z.read('classes.dex')

def uleb(buf, off):
    r = 0; s = 0
    while True:
        b = buf[off]; off += 1
        r |= (b & 0x7f) << s; s += 7
        if not b & 0x80: break
    return r, off

str_sz, str_off = struct.unpack_from('<II', dex, 56)
typ_sz, typ_off = struct.unpack_from('<II', dex, 64)
mth_sz, mth_off = struct.unpack_from('<II', dex, 88)
cls_sz, cls_off = struct.unpack_from('<II', dex, 96)

def gs(idx):
    o = struct.unpack_from('<I', dex, str_off + 4 * idx)[0]
    n, o = uleb(dex, o)
    return dex[o:o + n].decode('utf-8', 'replace')

def ts(idx):
    return gs(struct.unpack_from('<I', dex, typ_off + 4 * idx)[0])

def msig(idx):
    c, p, n = struct.unpack_from('<III', dex, mth_off + 8 * idx)
    return ts(c) + '->' + gs(n) + ts(p)

fid = 0
mid = 0
done = False
for ci in range(cls_sz):
    off = cls_off + 32 * ci
    cls, acc, sup = struct.unpack_from('<3I', dex, off)
    cdo = struct.unpack_from('<I', dex, off + 24)[0]
    if cdo == 0:
        if ts(cls) == desc:
            print(f'{desc} (class_def #{ci}) has NO class_data (marker class)')
            done = True
            break
        continue
    o = cdo
    sf, o = uleb(dex, o); inf, o = uleb(dex, o)
    dm, o = uleb(dex, o); vm, o = uleb(dex, o)
    for _ in range(sf + inf):
        d, o = uleb(dex, o); a, o = uleb(dex, o); fid += d
    entries = []
    for _ in range(dm + vm):
        d, o = uleb(dex, o); a, o = uleb(dex, o); co, o = uleb(dex, o)
        mid += d
        entries.append((mid, a, co))
    if ts(cls) == desc:
        print(f'{desc} extends {ts(sup)} (class_def #{ci})')
        for midx, a, co in entries:
            sig = msig(midx)
            name = sig.split('->')[1].split('(')[0]
            want = (mname is None) or (name == mname)
            tag = ' <<<' if want else ''
            print(f'  method idx={midx} {sig} access=0x{a:x} code_off=0x{co:x}{tag}')
            if name == mname and co and pc is not None:
                regs, ins, outs, tries, dbg, insns_sz, insns_off = \
                    struct.unpack_from('<7I', dex, co)
                lo = max(0, pc - before); hi = min(insns_sz, pc + after)
                print(f'  code: regs={regs} insns_sz={insns_sz} window [{lo},{hi})')
                for u in range(lo, hi):
                    cu = struct.unpack_from('<H', dex, insns_off * 2 + u * 2)[0]
                    op = (cu >> 8) & 0xFF
                    mark = ' <<<' if u == pc else ''
                    print(f'    pc={u:#06x} cu={cu:#06x} op={op:#04x}{mark}')
        done = True
    if done:
        break
if not done:
    sys.exit('class not found: ' + desc)
