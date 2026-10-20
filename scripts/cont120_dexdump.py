#!/usr/bin/env python3
"""CONT-120 vertical-vision dump: find a class/method in an APK's DEX files.

Usage: python3 scripts/cont120_dexdump.py <apk> <class-substring> [method-substring]
Prints matching class descriptors and, when a method filter is given, the
bytecode dump (reusing the EXP-051 dumper from miniandroid/tools).
"""
import sys
import zipfile

sys.path.insert(0, "/home/z/my-project/miniandroid/tools")
import dump_method_bytecode as d  # noqa: E402


def list_classes(data, needle):
    """Scan DEX string pool for type descriptors containing needle."""
    hits = []
    # string_ids at offset 56+4*idx per DEX header; simpler: regex the raw data
    # descriptors are length-prefixed MUTF-8 strings; the dumper already has a
    # DexFile class — use it and enumerate type_ids via its helpers if present.
    try:
        dex = d.DexFile(data, "raw")
        # Some dumpers expose strings; fall back to raw scan below.
        n = getattr(dex, "string_count", None)
    except Exception:
        dex = None
    raw = data
    token = needle.encode()
    start = 0
    while True:
        i = raw.find(token, start)
        if i < 0:
            break
        # backtrack to descriptor start: scan back to 'L' after a length byte
        j = i
        while j > 0 and raw[j - 1] != 0x00 and i - j < 220:
            j -= 1
            if raw[j:j + 1] == b"L":
                break
        s = raw[j:i + len(token) + 1]
        if s.startswith(b"L") and (b"/" in s):
            desc = s.rstrip(b";").decode("latin1") + ";"
            if desc not in hits:
                hits.append(desc)
        start = i + 1
        if len(hits) > 40:
            break
    return hits


def main():
    apk, needle = sys.argv[1], sys.argv[2]
    mneedle = sys.argv[3] if len(sys.argv) > 3 else None
    with zipfile.ZipFile(apk) as z:
        for dex_name in sorted(n for n in z.namelist() if n.endswith(".dex")):
            data = z.read(dex_name)
            hits = list_classes(data, needle)
            for desc in hits:
                if mneedle:
                    dex = d.DexFile(data, dex_name)
                    code_off, m = dex.find_method(desc, mneedle)
                    if code_off is not None:
                        print(f"=== {dex_name} :: {desc}.{mneedle} ===")
                        print(dex.dump_method(desc, mneedle))
                else:
                    print(f"{dex_name}: {desc}")


if __name__ == "__main__":
    main()
