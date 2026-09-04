#!/usr/bin/env python3
"""CAMPAIGN 010 R1 — join decoder TSVs, compute RGBA identity matrix."""
import csv, collections

rows = collections.defaultdict(dict)
for path, dec_key in [("/tmp/uc010_a.tsv", None), ("/tmp/uc010_b.tsv", None)]:
    with open(path) as fh:
        next(fh)  # first header line
        r = csv.DictReader(fh, delimiter="\t")
        for row in r:
            rows[row["file"]][row["decoder"]] = row

stats = collections.Counter()
mismatches = {"custom_vs_libpng": [], "custom_vs_stb": [], "libpng_vs_stb": []}
for f, d in rows.items():
    c, l, s = d.get("custom"), d.get("libpng"), d.get("stb230")
    if c and c["ok"] == "1": stats["custom_ok"] += 1
    if l and l["ok"] == "1": stats["libpng_ok"] += 1
    if s and s["ok"] == "1": stats["stb_ok"] += 1
    stats["total"] += 1
    if c and l:
        if c["ok"] == "1" and l["ok"] == "1":
            if c["rgba"] == l["rgba"]: stats["custom==libpng"] += 1
            else:
                stats["custom!=libpng"] += 1
                if len(mismatches["custom_vs_libpng"]) < 6: mismatches["custom_vs_libpng"].append(f)
        elif c["ok"] == "0" and l["ok"] == "0": stats["custom+libpng both fail"] += 1
    if l and s and l["ok"] == "1" and s["ok"] == "1":
        if l["rgba"] == s["rgba"]: stats["libpng==stb"] += 1
        else:
            stats["libpng!=stb"] += 1
            if len(mismatches["libpng_vs_stb"]) < 6: mismatches["libpng_vs_stb"].append(f)

n = stats["total"]
print(f"total files: {n}")
for k in ["custom_ok", "libpng_ok", "stb_ok", "custom==libpng", "custom!=libpng",
          "custom+libpng both fail", "libpng==stb", "libpng!=stb"]:
    print(f"  {k}: {stats[k]}")
print("\nmismatch examples:")
for k, v in mismatches.items():
    print(f"  {k}:")
    for x in v: print(f"    {x}")
