#!/usr/bin/env python3
"""cont11_cluster2.py — cluster by the precise API anchor inside NPE/CNF messages."""
import json, re, collections

OUT = "/home/z/my-project/run/cont11_census"
d = json.load(open(f"{OUT}/census.json"))

exc_class = collections.Counter()
api_anchor = collections.Counter()
crash_site = collections.Counter()
nsm_api = collections.Counter()
cnf_class = collections.Counter()

def parse(sig):
    exc = re.search(r"L([\w/$]+(?:Exception|Error));", sig)
    q = re.findall(r"'([^']+)'", sig)
    site = re.search(r"method=(\S+) pc=", sig)
    return (exc.group(1) if exc else None), (q[0] if q else None), (site.group(1) if site else None)

for r in d:
    sig = r.get("sig") or ""
    if not sig or sig in ("no-signal",):
        continue
    exc, api, site = parse(sig)
    if not exc:
        continue
    exc_class[exc] += 1
    if exc.endswith("NullPointerException") and api:
        api_anchor[api] += 1
    elif exc.endswith("ClassNotFoundException"):
        cnf_class[api or sig[:80]] += 1
    elif "NoSuchMethod" in (exc or ""):
        nsm_api[api or sig[:80]] += 1
    if site:
        crash_site[site.split(".")[0][:30]] += 1

print("=== exception classes across pool ===")
for k, c in exc_class.most_common(15):
    print(f"  {c:3d}  {k}")
print("\n=== NPE: invoked-API anchors (recurring cross-app) ===")
for k, c in api_anchor.most_common(40):
    if c >= 2:
        print(f"  {c:3d}  {k}")
print("\n=== NoSuchMethodError/Exception anchors ===")
for k, c in nsm_api.most_common(15):
    print(f"  {c:3d}  {k}")
print("\n=== ClassNotFoundException anchors ===")
for k, c in cnf_class.most_common(15):
    print(f"  {c:3d}  {k}")
