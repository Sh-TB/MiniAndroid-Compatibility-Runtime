#!/usr/bin/env python3
"""cont28_dooz_classes.py — list the dooz app-package classes in classes.dex,
plus which of them were initialized in the 120s baseline run (cross-ref diag).
Also: locate the game-screen composable classes the board depends on."""
import struct, sys, re

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
DIAG = "/home/z/my-project/run/cont18i/dooz_baseline/diag.txt"

data = open("/dev/null", "rb").read()  # placeholder
import zipfile
z = zipfile.ZipFile(APK)
data = z.read("classes.dex")

def u4(off): return struct.unpack_from("<I", data, off)[0]
def u2(off): return struct.unpack_from("<H", data, off)[0]

string_ids_size, string_ids_off = struct.unpack_from("<II", data, 0x38)
type_ids_size, type_ids_off = struct.unpack_from("<II", data, 0x40)
class_defs_size, class_defs_off = struct.unpack_from("<II", data, 0x60)

def get_string(idx):
    off = u4(string_ids_off + 4 * idx)
    p = off
    ln = 0; shift = 0
    while True:
        b = data[p]; p += 1
        ln |= (b & 0x7F) << shift; shift += 7
        if not (b & 0x80): break
    end = data.find(b"\x00", p)
    return data[p:end].decode("utf-8", "replace")

app_classes = []
for c in range(class_defs_size):
    off = class_defs_off + 32 * c
    t = u4(off)
    desc = get_string(u4(type_ids_off + 4 * t))
    if "yamin8000" in desc:
        app_classes.append(desc)

print(f"app classes total: {len(app_classes)}")
for d in app_classes:
    print(" ", d)

# cross-ref with diag: which were initialized
diag = open(DIAG, errors="replace").read()
inited = set(re.findall(r"\[CLASS_INIT\] class=(Lio/github/yamin8000/[A-Za-z0-9/_]+;)", diag))
print("\ninitialized in 120s run:", sorted(inited) if inited else "NONE")
