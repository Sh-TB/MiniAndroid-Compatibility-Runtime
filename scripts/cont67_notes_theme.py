#!/usr/bin/env python3
"""cont67_notes_theme.py — ground truth for the notes_secuso AppCompat gate:
(1) R$styleable.AppCompatTheme int[] from the DEX static values
(2) the style bag for SplashTheme(0x7f1201cc)/AppTheme(0x7f12000b) from
    resources.arsc (parent + attr ids)
"""
import zipfile, struct, sys

APK = 'upload/notes_secuso_105.apk'

z = zipfile.ZipFile(APK)
dex = None
for n in z.namelist():
    if n.endswith('.dex'):
        d = z.read(n)
        # quick string scan for the class name
        if b'Landroidx/appcompat/R$styleable;' in d:
            dex = d
            break
assert dex

def uleb(b, p):
    r = 0; s = 0
    while True:
        x = b[p]; p += 1
        r |= (x & 0x7f) << s
        if not (x & 0x80): return r, p
        s += 7

ssz, soff = struct.unpack_from('<II', dex, 0x38)
tsz, toff = struct.unpack_from('<II', dex, 0x40)
cdefsz, coff = struct.unpack_from('<II', dex, 0x60)

def s(i):
    o = struct.unpack_from('<I', dex, soff + 4*i)[0]
    ln, dp = uleb(dex, o)
    return dex[dp:dp+ln].decode('utf-8', 'replace')

def t(i):
    return s(struct.unpack_from('<I', dex, toff + 4*i)[0])

sv_off = None
for i in range(cdefsz):
    off = coff + 32*i
    ci = struct.unpack_from('<I', dex, off)[0]
    if t(ci) == 'Landroidx/appcompat/R$styleable;':
        sv_off = struct.unpack_from('<I', dex, off+28)[0]
        break
print('static_values_off', hex(sv_off))

# decode encoded_array: size, then values; we need the field names order —
# pair with class_data static field list (diffs ascending).
p = sv_off
cnt, p = uleb(dex, p)
vals = []
def dec_val(p):
    hdr = dex[p]; p += 1
    arg = hdr >> 5; typ = hdr & 0x1f
    nbytes = arg + 1
    raw = dex[p:p+nbytes]; p += nbytes
    v = int.from_bytes(raw, 'little')
    if typ == 0x1c:  # ARRAY
        arr = []
        q = p
        n, q = uleb(dex, q)
        for _ in range(n):
            v2, q = dec_val(q)
            arr.append(v2)
        return arr, q
    if typ == 0x00:  # BYTE
        return (v - 256 if v > 127 else v), p
    if typ == 0x02:  # SHORT
        return (v - (1 << (8*nbytes)) if v >> (8*nbytes - 1) else v), p
    if typ == 0x04:  # INT
        return (v - (1 << (8*nbytes)) if v >> (8*nbytes - 1) else v), p
    return v, p

for _ in range(cnt):
    v, p = dec_val(p)
    vals.append(v)
print('static values decoded:', len(vals))

# static field names via class_data
for i in range(cdefsz):
    off = coff + 32*i
    ci = struct.unpack_from('<I', dex, off)[0]
    if t(ci) == 'Landroidx/appcompat/R$styleable;':
        cv = struct.unpack_from('<I', dex, off+24)[0]
        q = cv
        sf, q = uleb(dex, q); inf, q = uleb(dex, q)
        dm, q = uleb(dex, q); vm, q = uleb(dex, q)
        names = []
        fi = 0
        for _ in range(sf):
            d1, q = uleb(dex, q); fi += d1
            a1, q = uleb(dex, q)
            names.append(fi)
        break
fsz, foff = struct.unpack_from('<II', dex, 0x50)
def fname(idx):
    c, ty, nm = struct.unpack_from('<HHI', dex, foff + 8*idx)
    return s(nm)

act_idx = None
for k, fid in enumerate(names):
    if fname(fid) == 'AppCompatTheme':
        act_idx = k
        break
print('AppCompatTheme at static idx', act_idx)
arr = vals[act_idx]
print('len', len(arr))
for i in range(min(len(arr), 140)):
    print(f'{i}: {arr[i]:#010x}')
