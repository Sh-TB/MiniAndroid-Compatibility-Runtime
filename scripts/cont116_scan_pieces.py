#!/usr/bin/env python3
"""cont116_scan_pieces.py — F-NEW-449 decode: find the method that builds the
Object[11] string-pieces array (aput-object pattern into new-array 0xb) inside
play_billing classes, then resolve its const-string pieces from the DEX string
pool and report raw bytes / MUTF-8 traps / lengths."""
import sys, zipfile, struct
sys.path.insert(0, "scripts")
from cont9_dexdump import Dex

APK = "upload/telegram_official.apk"
PKG = "Lcom/google/android/gms/internal/play_billing/"

z = zipfile.ZipFile(APK)
d = Dex(z.read("classes.dex"))

def iter_class_defs(d):
    for i in range(d.class_defs_size):
        off = d.u(d.class_defs_off + 32 * i, 4)
        yield off

def mutf8_len_check(raw):
    """Return (utf16_len, has_multibyte) for a MUTF-8 encoded string body."""
    n = 0; mb = False; i = 0
    while i < len(raw):
        b = raw[i]
        if b < 0x80:
            i += 1
        elif (b & 0xE0) == 0xC0:
            i += 2; mb = True; n += 1 if False else 0
        elif (b & 0xF0) == 0xE0:
            i += 3; mb = True
        else:
            i += 1
        n += 1
    return n, mb

hits = []
for cdef in iter_class_defs(d):
    desc = d.type_str(d.u(cdef, 4))
    if not desc.startswith(PKG):
        continue
    info = d.class_methods(cdef)
    for kind in ("direct", "virtual"):
        for mname, mdesc, acc, sz, code in info[kind]:
            if not code:
                continue
            # scan code units for new-array [Ljava/lang/Object; (op 0x24) preceded
            # by const/16 or const with 0xb, and >=8 aput-object (0x4d)
            units = [d.u(code + 2 * j, 2) for j in range(sz)]
            aput_obj = sum(1 for w in units if (w & 0xFF) == 0x4D)
            new_arr = sum(1 for w in units if (w & 0xFF) == 0x24)
            if new_arr and aput_obj >= 8:
                hits.append((desc, kind, mname, mdesc, sz, aput_obj, code))

print(f"candidate constructors: {len(hits)}")
for desc, kind, mname, mdesc, sz, aput, code in hits[:6]:
    print(f"== {desc} {kind} {mname}{mdesc} size={sz} aput-object={aput}")
    # disasm with cont9 and print const-string ops
    for line in d.disasm(code):
        if "const-string" in line or "new-array" in line:
            print("   ", line.strip()[:120])
