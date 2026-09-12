#!/usr/bin/env python3
"""S20: dump try/catch table of a method (binary-exact, dexformat.html law)."""
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

def sleb(p):
    r = s = 0
    while True:
        b = d[p + s]; r |= (b & 0x7f) << (7 * s); s += 1
        if not (b & 0x80):
            if b & 0x40 and s < 8: r -= (1 << (7 * s))
            return r, p + s

s_sz, s_off = u4(0x38), u4(0x3c)
t_sz, t_off = u4(0x40), u4(0x44)
m_sz, m_off = u4(0x58), u4(0x5c)
c_sz, c_off = u4(0x60), u4(0x64)
strs = []
for i in range(s_sz):
    off = u4(s_off + 4 * i); n, p = uleb(off)
    strs.append(d[p:p + n].decode('utf-8', 'replace'))
td = lambda i: strs[u4(t_off + 4 * i)]

co = None
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
            diff, p = uleb(p); af, p = uleb(p); c2, p = uleb(p)
            prev_m += diff
            if strs[u4(m_off + 8 * prev_m + 4)] == meth:
                co = c2
        if co: break
    if co: break

isz = u4(co + 12)
tries = u2(co + 6)
base = co + 16
tbase = base + 2 * isz
if tbase % 4: tbase += 2
print(f'{cls}.{meth}: insns_size={isz} tries={tries} try_table_off={tbase:#x}')
handlers = []
hlist_off = tbase + 8 * tries
n, p = uleb(hlist_off)
for h in range(n):
    hs, p = sleb(p)
    entry = []
    for c in range(abs(hs)):
        cty, p = uleb(p)
        addr, p = uleb(p)
        entry.append((cty, addr))
    if hs <= 0:
        addr, p = uleb(p)
        entry.append(('catch-all', addr))
    handlers.append(entry)
for i in range(tries):
    start, count, hoff = u2(tbase + 4 * i), u2(tbase + 4 * i + 2), u2(tbase + 4 * i + 4)
    # handler_off is from the START of the encoded_catch_handler_list
    hidx = None
    # compute which handler this offset refers to by walking offsets
    q = hlist_off
    _, q = uleb(q)
    for hi, hh in enumerate(handlers):
        if q - hlist_off == hoff:
            hidx = hi
        # re-walk to advance q
        szq, q2 = sleb(q)
        q = q2
        for c in range(abs(szq)):
            _, q = uleb(q); _, q = uleb(q)
        if szq <= 0:
            _, q = uleb(q)
    print(f'try[{i}]: pc=[{start:#x},{start+count:#x}) handler={handlers[hidx] if hidx is not None else hoff}')
