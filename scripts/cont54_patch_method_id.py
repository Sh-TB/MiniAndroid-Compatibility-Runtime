#!/usr/bin/env python3
"""CONT-54: byte-patch a method_id's class_idx inside a classes.dex —
reproduce the support-lib R8 artifact shape (child-class-owned owner of a
method NO DEX class declares) for the fnew326b probe variant.

Usage: cont54_patch_method_id.py <classes.dex> <from-class> <method-name> <to-class>
"""
import struct, sys

def uleb128(buf, off):
    r = 0; s = 0
    while True:
        b = buf[off]; off += 1
        r |= (b & 0x7f) << s
        if (b & 0x80) == 0: break
        s += 7
    return r, off

path, from_cls, mname, to_cls = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
d = bytearray(open(path, 'rb').read())
(sids, siof, tids, tiof, pids, piof, fids, fiof,
 mids, miof, cds, ciof) = struct.unpack_from('<12I', d, 56)

def s(idx):
    off = struct.unpack_from('<I', d, siof + 4*idx)[0]
    _, o = uleb128(d, off)
    end = d.index(b"\x00", o)
    return d[o:end].decode('utf-8', 'replace')

# locate the from/to type indices
def find_type(desc):
    for i in range(tids):
        si = struct.unpack_from('<I', d, tiof + 4*i)[0]
        if s(si) == desc:
            return i
    return None

from_idx = find_type(from_cls)
to_idx = find_type(to_cls)
if from_idx is None or to_idx is None:
    sys.exit(f"type not found: {from_cls}={from_idx} {to_cls}={to_idx}")

# patch every method_id (from_cls, mname) to to_cls
patched = 0
for i in range(mids):
    ci, proto = struct.unpack_from('<HH', d, miof + 8*i)
    nm, = struct.unpack_from('<I', d, miof + 8*i + 4)
    if ci == from_idx and s(nm) == mname:
        struct.pack_into('<H', d, miof + 8*i, to_idx)
        patched += 1

open(path, 'wb').write(d)
print(f"patched {patched} method_id(s) {from_cls}.{mname} -> {to_cls}")
if patched == 0:
    sys.exit(1)
