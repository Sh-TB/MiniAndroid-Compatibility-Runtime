#!/usr/bin/env python3
"""
g12_dex_class_scan.py — G11/G12 Phase 0/1 evidence: scan every cached corpus
APK's DEX files for CUSTOM classes whose superclass chain reaches a
framework View/ViewGroup/widget type.

Pure standard DEX format parsing (class_defs -> type_ids -> string_ids,
superclass_idx). No engine code paths. Output: JSON + human table listing
per APK: custom view classes, superclass, and (from manifest) whether the
class is referenced from XML layouts is NOT determined here (that is the
runtime trace's job).

Usage: python3 g12_dex_class_scan.py [--apk NAME_FILTER]
"""
import json
import struct
import sys
import zipfile
from pathlib import Path

REPO = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
CACHE = REPO / "miniandroid" / "download"
OUT = REPO / "docs" / "evidence" / "g11g12_evidence"

FRAMEWORK_PREFIXES = (
    "Landroid/view/", "Landroid/widget/", "Landroid/webkit/",
    "Landroid/text/", "Landroid/support/", "Landroidx/",
    "Lcom/google/android/material/", "Ljava/", "Ljavax/",
    "Ldalvik/", "Lkotlin",
)


def uleb128(buf, off):
    result = 0
    shift = 0
    while True:
        b = buf[off]
        off += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, off
        shift += 7


def parse_dex(data: bytes, dex_name: str):
    """Return list of (class_descriptor, super_descriptor) for class_defs."""
    if data[:4] != b"dex\n":
        return []
    string_ids_size, string_ids_off = struct.unpack_from("<II", data, 0x38)
    type_ids_size, type_ids_off = struct.unpack_from("<II", data, 0x40)
    class_defs_size, class_defs_off = struct.unpack_from("<II", data, 0x60)

    def get_str(idx):
        if idx >= string_ids_size:
            return None
        (so,) = struct.unpack_from("<I", data, string_ids_off + idx * 4)
        _, p = uleb128(data, so)
        end = data.index(b"\x00", p)
        return data[p:end].decode("utf-8", "replace")

    def get_type(idx):
        if idx >= type_ids_size:
            return None
        (si,) = struct.unpack_from("<I", data, type_ids_off + idx * 4)
        return get_str(si)

    out = []
    for i in range(class_defs_size):
        base = class_defs_off + i * 32
        (class_idx, access, super_idx) = struct.unpack_from("<III", data, base)
        cls = get_type(class_idx)
        sup = get_type(super_idx) if super_idx != 0xFFFFFFFF else None
        out.append((cls, sup))
    return out


def view_root(sup_chain_map, desc, depth=0):
    """Walk super chain; return the first framework ancestor descriptor."""
    seen = set()
    while desc and desc not in seen and depth < 32:
        seen.add(desc)
        sup = sup_chain_map.get(desc)
        if sup is None:
            return None
        if sup.startswith(FRAMEWORK_PREFIXES):
            return sup
        desc = sup
        depth += 1
    return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    apk_filter = None
    if len(sys.argv) > 2 and sys.argv[1] == "--apk":
        apk_filter = sys.argv[2].lower()

    results = []
    for apk in sorted(CACHE.rglob("*.apk")):
        if apk_filter and apk_filter not in apk.name.lower():
            continue
        entry = {"apk": apk.name, "dex_files": 0, "custom_views": []}
        try:
            with zipfile.ZipFile(apk) as z:
                dex_names = [n for n in z.namelist()
                             if n.endswith(".dex")]
                entry["dex_files"] = len(dex_names)
                for dn in dex_names:
                    data = z.read(dn)
                    pairs = parse_dex(data, dn)
                    chain = {c: s for c, s in pairs}
                    for cls, sup in pairs:
                        if sup is None:
                            continue
                        # custom = superclass is framework view-ish, class is app code
                        if sup.startswith(FRAMEWORK_PREFIXES):
                            if sup.startswith(
                                ("Landroid/view/", "Landroid/widget/",
                                 "Landroid/webkit/")):
                                entry["custom_views"].append(
                                    {"class": cls, "direct_super": sup,
                                     "dex": dn})
                        else:
                            root = view_root(chain, cls)
                            if root and root.startswith(
                                ("Landroid/view/", "Landroid/widget/",
                                 "Landroid/webkit/")):
                                entry["custom_views"].append(
                                    {"class": cls, "direct_super": sup,
                                     "view_root": root, "dex": dn})
        except Exception as e:  # noqa: BLE001
            entry["error"] = repr(e)
        results.append(entry)

    out_json = OUT / "g12_custom_view_scan.json"
    out_json.write_text(json.dumps(results, indent=1))
    for e in results:
        print(f"== {e['apk']}  dex_files={e['dex_files']}")
        for cv in e.get("custom_views", []):
            root = cv.get("view_root", "")
            print(f"   {cv['class']}  <- {cv['direct_super']}"
                  + (f"  (root {root})" if root else ""))
    print(f"\nwrote {out_json}")


if __name__ == "__main__":
    main()
