#!/usr/bin/env python3
"""S20: decode D.a code_item header + invoke-virtual/range receiver registers.

Format law (dexformat.html):
  code_item: registers_size(u2) ins_size(u2) outs_size(u2) tries_size(u2)
             debug_info_off(u4) insns_size(u4) insns...
  3rm (invoke-*-range): AA|op, BBBB=method_idx, CCCC=first register (AA=size)
"""
import struct, sys, zipfile

apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
d = zipfile.ZipFile(apk).read('classes.dex')
u4 = lambda o: struct.unpack_from('<I', d, o)[0]
u2 = lambda o: struct.unpack_from('<H', d, o)[0]

def uleb(p):
    r = s = 0
    while True:
        b = d[p + s]; r |= (b & 0x7f) << (7 * s); s += 1
        if not (b & 0x80): return r, p + s

s_sz, s_off = u4(0x38), u4(0x3c)
t_sz, t_off = u4(0x40), u4(0x44)
m_sz, m_off = u4(0x58), u4(0x5c)
c_sz, c_off = u4(0x60), u4(0x64)
strs = []
for i in range(s_sz):
    off = u4(s_off + 4 * i); n, p = uleb(off)
    strs.append(d[p:p + n].decode('utf-8', 'replace'))
td = lambda i: strs[u4(t_off + 4 * i)]

def method_ref(i):
    o = m_off + 8 * i
    return td(u2(o)), strs[u4(o + 4)]

target_code = None
for i in range(c_sz):
    o = c_off + 32 * i
    if td(u4(o)) != cls: continue
    cdo = u4(o + 24)
    if cdo == 0: continue
    n_sf, p = uleb(cdo); n_if_, p = uleb(p); n_dm, p = uleb(p); n_vm, p = uleb(p)
    prev = 0
    for _ in range(n_sf):
        _, p = uleb(p); _, p = uleb(p)
    for _ in range(n_if_):
        _, p = uleb(p); _, p = uleb(p)
    for kind, cnt in (('direct', n_dm), ('virtual', n_vm)):
        prev_m = 0
        for _ in range(cnt):
            diff, p = uleb(p); af, p = uleb(p); co, p = uleb(p)
            prev_m += diff
            mo = m_off + 8 * prev_m
            name = strs[u4(mo + 4)]
            if name == meth:
                target_code = (kind, name, co)
                print(f'FOUND {cls}.{meth} [{kind}] code_off={co}')
                break
        if target_code: break
    if target_code: break

if not target_code:
    sys.exit('method not found')

_, _, co = target_code
regs = u2(co); ins = u2(co + 2); outs = u2(co + 4); tries = u2(co + 6)
dbg = u4(co + 8); isz = u4(co + 12)
print(f'registers_size={regs} ins_size={ins} outs_size={outs} tries={tries} '
      f'debug_info_off={dbg:#x} insns_size={isz}')
print(f'params occupy v{regs - ins}..v{regs - 1}')

base = co + 16
# find every invoke-*-range (0x74..0x78) and print receiver; also print
# every invoke-virtual with explicit regs (0x6e) on View methods of interest
pc = 0
while pc < isz:
    w = u2(base + 2 * pc)
    op = w & 0xff
    if op in (0x74, 0x75, 0x76, 0x77, 0x78):
        mi = u2(base + 2 * (pc + 1))
        size_first = u2(base + 2 * (pc + 2))
        first = size_first & 0xff
        size = size_first >> 8
        mcls, mname = method_ref(mi)
        mark = ' <<<' if 'getParent' in mname or 'getViewTreeOwners' in mname else ''
        print(f'pc={pc:#06x} op={op:#04x} {mcls}.{mname} range=v{first}..v{first+size-1}{mark}')
        pc += 3
        continue
    if op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
        mi = u2(base + 2 * (pc + 1))
        mcls, mname = method_ref(mi)
        if 'getParent' in mname or 'getViewTreeOwners' in mname:
            # 35c: A|G|op BBBB FEDC — regs in nibbles D,C,F,E,G (low-to-high per AOSP)
            w1 = u2(base + 2 * (pc + 2))
            A = (w >> 12) & 0xf; G = (w >> 8) & 0xf
            C = w1 & 0xf; D_ = (w1 >> 4) & 0xf; E = (w1 >> 8) & 0xf; F_ = (w1 >> 12) & 0xf
            regs_list = [C, D_, E, F_, G][:A] if A <= 5 else []
            print(f'pc={pc:#06x} op={op:#04x} {mcls}.{mname} regs={regs_list} '
                  f'(receiver={regs_list[0] if regs_list else "?"}) <<<')
        pc += 3
        continue
    sz = 1
    if op in (0x00,) :
        if w == 0x0100: sz = 2
    elif op >= 0x02 and op in (0x02, 0x03, 0x04, 0x05, 0x06, 0x08, 0x09, 0x0a):
        sz = 2
    # coarse: use minidump ordering — simplest: reuse known table
    pc += sz
