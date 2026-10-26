#!/usr/bin/env python3
"""CONT-41 — census retention gate: compare evidence/cont41/batch50_census.json
against evidence/cont40/batch50_census.json. The 13 content rows MUST retain
byte-exact screenshot sha (regression contract); report any new content rows
(crossings) and any sha drift."""
import json, sys

c40 = {r["label"]: r for r in json.load(open("/home/z/my-project/evidence/cont40/batch50_census.json"))}
c41 = {r["label"]: r for r in json.load(open("/home/z/my-project/evidence/cont41/batch50_census.json"))}

def px(r): return (r.get("png") or {}).get("content_px", 0) or 0
def sha(r): return r.get("screenshot_sha16")

content40 = {l for l, r in c40.items() if px(r) >= 1000}
content41 = {l for l, r in c41.items() if px(r) >= 1000}

print(f"rows: cont40={len(c40)} cont41={len(c41)}")
print(f"content rows: cont40={len(content40)} cont41={len(content41)}")

drift = []
for l in sorted(content40 & content41):
    s40, s41 = sha(c40[l]), sha(c41[l])
    mark = "OK " if s40 == s41 else "DRIFT"
    if s40 != s41:
        drift.append(l)
    print(f"  [{mark}] {l:20s} {s40} -> {s41} px {px(c40[l])} -> {px(c41[l])}")

new = content41 - content40
lost = content40 - content41
if new: print(f"\nNEW CROSSINGS: {sorted(new)}")
if lost: print(f"\nLOST CONTENT (REGRESSION): {sorted(lost)}")
if drift: print(f"\nSHA DRIFT: {drift}")
print(f"\nVERDICT: {'PASS' if not drift and not lost else 'FAIL'}")
