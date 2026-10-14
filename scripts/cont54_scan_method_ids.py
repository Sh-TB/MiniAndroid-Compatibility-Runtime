#!/usr/bin/env python3
"""CONT-54: scan ALL method_ids named getChildMeasureSpec + all declaring
classes with that method — establish the TRUE resolution target. v2 with
proper proto_ids resolution + bounds safety."""
import struct, sys, zipfile

def uleb128(buf, off):
    r = 0; s = 0
    while True:
        b = buf[off]; off += 1
        r |= (b & 0x7f) << s
        if (b & 0x80) == 0: break
        s += 7
    return r, off

z = zipfile.ZipFile('upload/cont50_apks/de.tobiasbielefeld.solitaire_71.apk')
d = z.read('classes.dex')
(sids, siof, tids, tiof, pids, piof, fids, fiof, mids, miof, cds, ciof) = struct.unpack_from('<12I', d, 56)

def s(idx):
    if idx >= sids: return f"<str{idx}>"
    off = struct.unpack_from('<I', d, siof + 4*idx)[0]
    _, o = uleb128(d, off)
    end = d.index(b"\x00", o)
    return d[o:end].decode('utf-8', 'replace')

def t(idx):
    if idx >= tids: return f"<type{idx}>"
    return s(struct.unpack_from('<I', d, tiof + 4*idx)[0])

def proto_sig(pidx):
    if pidx >= pids: return f"<proto{pidx}>"
    off = piof + 12*pidx
    shorty, ret, params = struct.unpack_from('<3I', d, off)
    ps = ''
    if params:
        (pn,) = struct.unpack_from('<I', d, params)
        for k in range(pn):
            ti = struct.unpack_from('<H', d, params + 2 + 2*k)[0]
            ps += t(ti)
    return f"({ps}){t(ret)}"

print("=== method_ids named getChildMeasureSpec ===")
for i in range(mids):
    ci, proto = struct.unpack_from('<HH', d, miof + 8*i)
    nm, = struct.unpack_from('<I', d, miof + 8*i + 4)
    if s(nm) == 'getChildMeasureSpec':
        print(f"  m@{i} cls={t(ci)} sig={proto_sig(proto)}")

print("=== declaring classes (scan all class_defs safely) ===")
for ci_def in range(cds):
    off = ciof + 32*ci_def
    class_idx, acc, sup, ifaces, src, ann, cdata, svals = struct.unpack_from('<8I', d, off)
    cls = t(class_idx)
    if not cdata: continue
    try:
        o = cdata
        sf, o = uleb128(d, o); inf, o = uleb128(d, o)
        dm, o = uleb128(d, o); vm, o = uleb128(d, o)
        for kind, count in (('direct', dm), ('virtual', vm)):
            last = 0
            for _ in range(count):
                mi, o = uleb128(d, o); mi += last; last = mi
                a, o = uleb128(d, o)
                co, o = uleb128(d, o)
                if mi >= mids: raise ValueError("method idx overflow")
                c2, pr = struct.unpack_from('<HH', d, miof + 8*mi)
                nm2, = struct.unpack_from('<I', d, miof + 8*mi + 4)
                if s(nm2) == 'getChildMeasureSpec':
                    print(f"  {cls} ({kind}) sig={proto_sig(pr)} code_off={co} acc={a:#x} super={t(sup)}")
    except (ValueError, struct.error):
        continue

print("=== DrawerLayout super chain ===")
sup_map = {}
for ci_def in range(cds):
    off = ciof + 32*ci_def
    class_idx, acc, sup = struct.unpack_from('<3I', d, off)
    sup_map[t(class_idx)] = t(sup)
cur = 'Landroid/support/v4/widget/DrawerLayout;'
chain = []
while cur in sup_map and len(chain) < 12:
    nxt = sup_map[cur]
    chain.append(f"{cur} -> {nxt}")
    cur = nxt
for c in chain: print("  " + c)
