#!/usr/bin/env python3
"""cont375_find_class.py — search a APK's dex classes for original/renamed names."""
import sys, zipfile, struct, re

APK = sys.argv[1]
NEEDLE = sys.argv[2] if len(sys.argv) > 2 else "AndroidCompositionLocals"

z = zipfile.ZipFile(APK)
dexes = [n for n in z.namelist() if n.endswith('.dex')]
print(f"{len(dexes)} dex files")

def read_uleb(b, off):
    result = 0; shift = 0
    while True:
        byte = b[off]; off += 1
        result |= (byte & 0x7f) << shift
        if not (byte & 0x80): break
        shift += 7
    return result, off

def get_strings(b):
    """Return list of strings from dex string_ids."""
    string_ids_size, string_ids_off = struct.unpack_from('<II', b, 56)
    strings = []
    for i in range(string_ids_size):
        data_off, = struct.unpack_from('<I', b, string_ids_off + i*4)
        n, off = read_uleb(b, data_off)
        end = b.index(b'\x00', off)
        strings.append(b[off:end].decode('utf-8', 'replace'))
    return strings

for name in dexes:
    b = z.read(name)
    try:
        strings = get_strings(b)
    except Exception as e:
        print(name, 'parse fail:', e); continue
    hits = [s for s in strings if NEEDLE.lower() in s.lower()]
    print(f"{name}: {len(strings)} strings, hits for '{NEEDLE}':")
    for h in hits[:12]:
        print("   ", h[:120])
