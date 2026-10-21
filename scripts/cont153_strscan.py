#!/usr/bin/env python3
"""cont153_strscan.py — locate Lpz0;/Lwt0;/Lkz0;/Lel0; in telegram dex string tables."""
import zipfile, struct

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1; r |= (x & 0x7f) << s
        if not (x & 0x80): break
        s += 7
    return r, o

zf = zipfile.ZipFile('upload/forkgram_709208.apk')
TARGETS = {'Lpz0;', 'Lwt0;', 'Lkz0;', 'Lel0;', 'Lpz0;', 'Lpz0;.T0', 'T0'}
for dn in sorted(n for n in zf.namelist() if n.startswith('classes') and n.endswith('.dex')):
    dex = zf.read(dn)
    str_size, str_off = struct.unpack_from('<2I', dex, 0x38)
    soa = struct.unpack_from(f'<{str_size}I', dex, str_off)
    hits = []
    for si in range(str_size):
        off = soa[si]; _, o = uleb(dex, off)
        e = dex.index(b'\x00', o)
        s = dex[o:e].decode('utf-8', 'replace')
        if s in TARGETS or s.startswith('Lpz0') or s.startswith('Lwt0') or s.startswith('Lkz0') or s.startswith('Lel0'):
            hits.append((si, s))
    print(dn, 'strings:', str_size, 'hits:', hits[:10])
