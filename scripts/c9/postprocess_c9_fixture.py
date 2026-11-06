#!/usr/bin/env python3
"""scripts/c9/postprocess_c9_fixture.py — pin ZIP storage laws + determinism
for the CODER 9 fixture APK, and print the evidence table.

Pins (the aapt2/apk packaging may choose methods freely; the harness needs
EXACT storage classes for CASE04/CASE05):
  assets/c9_stored.bin     → method 0 (STORED)   — AFD data-offset law case
  assets/c9_compressed.txt → method 8 (DEFLATE)  — openFd-refusal law case
All entries: fixed 1980 epoch, normalized order → byte-deterministic APK.

Prints per-entry: method, sizes, LFH data_offset (independent APPNOTE §4.3.7
arithmetic) and the SHA-256 of every pinned payload, for the validator.
"""
import hashlib
import struct
import sys
import zipfile
import zlib

FIXED_DATE = (1980, 1, 1, 0, 0, 0)


def main() -> None:
    apk = sys.argv[1]
    with zipfile.ZipFile(apk, "r") as zin:
        names = zin.namelist()
        payload = {n: zin.read(n) for n in names}

    def method_for(name: str, current: int) -> int:
        if name == "assets/c9_stored.bin":
            return zipfile.ZIP_STORED
        if name == "assets/c9_compressed.txt":
            return zipfile.ZIP_DEFLATED
        return current

    with zipfile.ZipFile(apk, "w") as zout:
        for n in names:
            info = zipfile.ZipInfo(n, date_time=FIXED_DATE)
            info.compress_type = method_for(n, zipfile.ZIP_STORED)
            info.external_attr = 0o644 << 16
            zout.writestr(info, payload[n])

    # ── Evidence table: independent data_offset arithmetic per APPNOTE ──
    data = open(apk, "rb").read()
    print("== C9 fixture post-processed ==")
    with zipfile.ZipFile(apk, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            lfh_off = info.header_offset
            nlen, xlen = struct.unpack_from("<HH", data, lfh_off + 26)
            data_off = lfh_off + 30 + nlen + xlen
            if info.filename in ("assets/c9_stored.bin",
                                 "assets/c9_compressed.txt",
                                 "assets/sub/deep/c9_nested.bin"):
                sha = hashlib.sha256(payload[info.filename]).hexdigest()
                print(f"PINNED {info.filename}: method={info.compress_type} "
                      f"lfh={lfh_off} data_offset={data_off} "
                      f"csize={info.compress_size} sha256={sha}")
            elif info.filename in ("AndroidManifest.xml", "resources.arsc",
                                   "classes.dex"):
                print(f"OK    {info.filename}: method={info.compress_type} "
                      f"data_offset={data_off}")
    print("APK SHA-256:", hashlib.sha256(data).hexdigest())
    print("APK bytes:", len(data))


if __name__ == "__main__":
    main()
