#!/usr/bin/env python3
"""Dump a DEX string by string_ids index (probe for updater field names)."""
import struct, sys, zipfile

def load_dex(path):
    with zipfile.ZipFile(path) as z:
        return z.read('classes.dex')

def u32(b, o): return struct.unpack_from('<I', b, o)[0]

def string_at(dex, idx):
    table = u32(dex, 0x3C)          # string_ids_off VALUE lives at header 0x3C
    off = u32(table + 4 * idx)
    # uleb128 length
    p = off; result = 0; shift = 0
    while True:
        b = dex[p]; p += 1
        result |= (b & 0x7f) << shift
        shift += 7
        if not (b & 0x80): break
    end = dex.find(b'\x00', p)
    return dex[p:end].decode('utf-8', 'replace')

def main():
    dex = load_dex(sys.argv[1])
    for idx in sys.argv[2:]:
        print(f"idx {idx}: {string_at(dex, int(idx))!r}")

if __name__ == '__main__':
    main()
