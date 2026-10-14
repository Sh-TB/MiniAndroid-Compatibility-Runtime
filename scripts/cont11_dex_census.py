#!/usr/bin/env python3
"""CONT-11: census of Fragment/Preference family classes in an APK's DEX.
Reads the DEX string_ids + type_ids and lists class descriptors matching
the Fragment/Preference families. Read-only evidence tool."""
import sys, zipfile, struct

def read_dex_strings(data):
    """Return the list of MUTF-8 strings in the dex string_ids table."""
    if data[:4] != b'dex\n':
        return []
    string_ids_size, string_ids_off = struct.unpack_from('<II', data, 56)
    strings = []
    for i in range(string_ids_size):
        (soff,) = struct.unpack_from('<I', data, string_ids_off + i * 4)
        # uleb128 length then MUTF-8 bytes until NUL
        p = soff
        result = 0
        shift = 0
        while True:
            b = data[p]; p += 1
            result |= (b & 0x7f) << shift
            if not (b & 0x80):
                break
            shift += 7
        end = data.index(b'\x00', p)
        strings.append(data[p:end].decode('utf-8', 'replace'))
    return strings

def main():
    apk = sys.argv[1]
    pats = [p.lower() for p in sys.argv[2:]] or ['fragment', 'preference']
    z = zipfile.ZipFile(apk)
    for name in sorted(n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')):
        data = z.read(name)
        strings = read_dex_strings(data)
        # class descriptors look like L....;
        classes = sorted(s for s in strings if s.startswith('L') and s.endswith(';') and '/' in s)
        hits = set()
        for c in classes:
            lc = c.lower()
            if any(p in lc for p in pats):
                hits.add(c)
        print(f"== {name}: {len(classes)} classes, {len(hits)} family hits")
        for c in sorted(hits):
            print("  ", c)

if __name__ == '__main__':
    main()
