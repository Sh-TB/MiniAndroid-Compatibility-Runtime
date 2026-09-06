#!/usr/bin/env python3
"""
g12_axml_custom_ref_scan.py (v2) — for each corpus APK, scan binary layout
XMLs (res/layout*) string pools for references to app-code custom classes
found by g12_dex_class_scan.py. Handles dot-form class names
(com.example.MyView) and substring matching. G11/G12 subset-selection
evidence.
"""
import json
import struct
import zipfile
from pathlib import Path

REPO = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
CACHE = REPO / "miniandroid" / "download"
OUT = REPO / "docs" / "evidence" / "g11g12_evidence"

SCAN = json.loads((OUT / "g12_custom_view_scan.json").read_text())
LIB_PREFIXES = ("Landroidx/", "Landroid/support/",
                "Lcom/google/android/material/", "Landroidx/compose/")


def custom_classes(entry):
    out = []
    for cv in entry.get("custom_views", []):
        c = cv["class"]
        if c.startswith(LIB_PREFIXES):
            continue
        out.append(c)
    return out


def axml_strings(data: bytes):
    """Minimal AXML ResStringPool reader (UTF-8 and UTF-16 variants)."""
    if len(data) < 16 or data[:2] != b"\x03\x00":
        return []
    chunk_type, hdr_size, chunk_size = struct.unpack_from("<HHI", data, 8)
    if chunk_type != 0x0001:  # RES_STRING_POOL_TYPE
        return []
    base = 8
    str_count = struct.unpack_from("<I", data, base + 8)[0]
    flags = struct.unpack_from("<I", data, base + 16)[0]
    strings_start = base + struct.unpack_from("<I", data, base + 20)[0]
    is_utf8 = bool(flags & (1 << 8))
    out = []
    for i in range(str_count):
        off = base + 28 + i * 4
        if off + 4 > len(data):
            break
        so = struct.unpack_from("<I", data, off)[0]
        p = strings_start + so
        if p >= len(data):
            continue
        try:
            if is_utf8:
                n = data[p]; p += 1
                if n & 0x80:
                    n = ((n & 0x7F) << 8) | data[p]; p += 1
                ln = data[p]; p += 1
                if ln & 0x80:
                    ln = ((ln & 0x7F) << 8) | data[p]; p += 1
                out.append(data[p:p + ln].decode("utf-8", "replace"))
            else:
                n = data[p] | (data[p + 1] << 8); p += 2
                if n & 0x8000:
                    n2 = data[p] | (data[p + 1] << 8); p += 2
                    n = ((n & 0x7FFF) << 16) | n2
                out.append(data[p:p + n * 2].decode("utf-16-le", "replace"))
        except Exception:  # noqa: BLE001
            continue
    return out


def main():
    report = {}
    for entry in SCAN:
        hits = list(CACHE.rglob(entry["apk"]))
        if not hits:
            continue
        apk_path = hits[0]
        customs = custom_classes(entry)
        if not customs:
            continue
        # search keys: descriptor form, dot form, short leaf
        needles = set()
        for c in customs:
            leaf = c.rstrip(";").split("/")[-1]
            dots = c[1:-1].replace("/", ".") if c.startswith("L") else c
            needles.add(leaf)
            needles.add(dots)
        found = {}
        try:
            with zipfile.ZipFile(apk_path) as z:
                for n in sorted(z.namelist()):
                    if not n.startswith("res/layout"):
                        continue
                    strs = axml_strings(z.read(n))
                    used = sorted({s for s in strs
                                   if any(nd in s for nd in needles)})
                    if used:
                        found[n] = used
        except Exception as e:  # noqa: BLE001
            found["ERROR"] = [repr(e)]
        report[entry["apk"]] = {"custom_classes": customs,
                                "layout_refs": found}
        flag = "YES" if any(not k.startswith("ERROR") for k in found) else "no"
        print(f"{entry['apk']:46s} {flag}")
        for k, v in sorted(found.items()):
            print(f"    {k}: {v}")
    (OUT / "g12_axml_custom_ref_scan.json").write_text(
        json.dumps(report, indent=1))
    print(f"\nwrote {OUT/'g12_axml_custom_ref_scan.json'}")


if __name__ == "__main__":
    main()
