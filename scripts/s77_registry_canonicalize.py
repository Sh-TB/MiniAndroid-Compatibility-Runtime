#!/usr/bin/env python3
"""s77_registry_canonicalize.py — S77 §2: canonicalize the registry.

1. Fix the stale scalar `total` (397) → actual roots length (404).
   summary.total_roots and len(roots) were already 404; only `total` lagged.
2. Append an explicit canonicalization note: F-151 numbering gap is CONFIRMED
   (no record with ID F-151 was ever registered; F-152/F-153 are the canonical
   S76 failure IDs — the S76 report's numbering is correct).
3. Re-assert commit accounting facts in the note (8 unpublished = 5 S75 + 3 S76).
"""
import json

REG = "/home/z/my-project/root_registry.json"
with open(REG) as f:
    d = json.load(f)

before = d.get("total")
n = len(d["roots"])
d["total"] = n

note = (
    " || S77 CANONICALIZATION (2026-09-22): stale scalar total "
    f"{before} -> {n} (summary.total_roots and roots length were already {n}; "
    "no records added or removed). F-NUMBERING RESOLVED: F-151 is a confirmed "
    "numbering gap — no record with ID F-151 was ever registered (next-free-id "
    "scan at S76 jumped it); F-152 (dooz Llt0;.w pc=808 null receiver) and "
    "F-153 (dialog CJK label paint) are the canonical S76 failure IDs. "
    "ROOT COUNT 397->404 enumerated exactly: R-NEW-390 (File.getAbsoluteFile), "
    "R-NEW-391 (File.getCanonicalFile/Path), R-NEW-392 (TextView subsumption), "
    "R-NEW-393 (View.getBackground themed-widget + Drawable.setColorFilter), "
    "R-NEW-394 (dialog decor layout + topmost-window touch), F-152, F-153. "
    "COMMIT ACCOUNTING: 8 unpublished commits at S77 start = 5 S75 carry-over "
    "(affc0d57, 310aba44, 84ac7869, 2835e9c6, b326acfd) + 3 S76 "
    "(2f13abe2, 3057ddb3, a8704916); origin/main = c67230be (ls-remote verified). "
    "PUBLISH: PUBLISH_BLOCKED (no GH_TOKEN in session; constitution §52)."
)
d["summary"]["note"] = str(d["summary"].get("note", "")) + note

with open(REG, "w") as f:
    json.dump(d, f, indent=1, ensure_ascii=False)
print(f"total: {before} -> {d['total']}; roots={n}; note appended")
