#!/usr/bin/env python3
"""CONT-55: parse the sparse-switch payload of NavigationView.onMeasure —
the mode->case mapping decides which branch the AT_MOST drawer spec takes."""
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
(sids, siof, tids, tiof, pids, piof, fids, fiof,
 mids, miof, cds, ciof) = struct.unpack_from('<12I', d, 56)

def s(idx):
    off = struct.unpack_from('<I', d, siof + 4*idx)[0]
    _, o = uleb128(d, off)
    end = d.index(b"\x00", o)
    return d[o:end].decode('utf-8', 'replace')

def t(idx):
    return s(struct.unpack_from('<I', d, tiof + 4*idx)[0])

# find DrawerLayout.onMeasure code_off
target = 'Landroid/support/design/widget/NavigationView;'
cls_off = None
for i in range(cds):
    off = ciof + 32*i
    class_idx, acc, sup = struct.unpack_from('<3I', d, off)
    if t(class_idx) == target:
        cls_off = off; break
o = struct.unpack_from('<I', d, cls_off + 28)[0]  # class_data_off
sf, o = uleb128(d, o); inf, o = uleb128(d, o); dm, o = uleb128(d, o); vm, o = uleb128(d, o)
last = 0
found = None
for _ in range(sf + inf):
    fi, o = uleb128(d, o)
    a, o = uleb128(d, o)  # field lists: pairs, no cross-list continuity needed
last = 0
for _ in range(dm):
    mi, o = uleb128(d, o); mi += last; last = mi
    a, o = uleb128(d, o)
    co, o = uleb128(d, o)
    ci2, pr = struct.unpack_from('<HH', d, miof + 8*mi)
    nm, = struct.unpack_from('<I', d, miof + 8*mi + 4)
    if s(nm) == 'onMeasure' and co:
        found = co
last = 0
for _ in range(vm):
    mi, o = uleb128(d, o); mi += last; last = mi
    a, o = uleb128(d, o)
    co, o = uleb128(d, o)
    ci2, pr = struct.unpack_from('<HH', d, miof + 8*mi)
    nm, = struct.unpack_from('<I', d, miof + 8*mi + 4)
    if s(nm) == 'onMeasure' and co:
        found = co
if not found:
    sys.exit("onMeasure not found")

registers, ins, outs, tries, dbg, insns = struct.unpack_from('<6H', d, found)
(insns_size,) = struct.unpack_from('<I', d, found + 12)
base = found + 16
units = struct.unpack_from(f'<{insns_size}H', d, base)
print(f"NavigationView.onMeasure: {insns_size} units")

# walk to find the sparse-switch at pc=6 and its payload
i = 6
op = units[6] & 0xff
print(f"@0x0006 unit=0x{units[6]:04x} op={op:#x}")
assert op == 0x2c, "expected sparse-switch"
# sparse-switch: 2 units + identBBBB; payload is BRANCH-RELATIVE:
# payload_addr = pc + signed(units[pc+1])
off_units = units[7]
off_units = off_units - 0x10000 if off_units > 0x7fff else off_units
payload_pc = 6 + off_units
print(f"payload at unit 0x{payload_pc:04x}")
ident, psize = struct.unpack_from('<HH', d, base + 2*payload_pc)
print(f"payload ident=0x{ident:04x} size={psize}")
targets = struct.unpack_from(f'<{psize}i', d, base + 2*payload_pc + 4)
keys = struct.unpack_from(f'<{psize}i', d, base + 2*payload_pc + 4 + 4*psize)
names = {0: 'UNSPECIFIED', 0x40000000: 'EXACTLY', (int)(0x80000000): 'AT_MOST'}
for k in range(psize):
    nm = names.get(keys[k], f'0x{keys[k] & 0xffffffff:08x}')
    print(f"  key {nm} (0x{keys[k] & 0xffffffff:08x}) -> case @0x{(payload_pc + targets[k]):04x}")
