#!/usr/bin/env python3
"""cont11_cluster.py — deep-cluster the census by exception message content:
missing classes, missing methods, and recurring NPE message roots."""
import json, re, collections, os

OUT = "/home/z/my-project/run/cont11_census"
d = json.load(open(f"{OUT}/census.json"))

cnf = collections.Counter()
nsm = collections.Counter()
npe_msgs = collections.Counter()
fam_members = collections.defaultdict(list)

def msg_of(sig):
    m = re.search(r"\((.*?)\)\s+method=", sig)
    if m:
        return m.group(1)
    m = re.search(r'msg="(.*?)"', sig)
    return m.group(1) if m else sig

for r in d:
    fam = r.get("family")
    fam_members[fam].append(r["apk"])
    sig = r.get("sig") or ""
    if fam == "CLASSNOTFOUND":
        m = re.search(r"L([\w/$]+);", sig)
        cnf[m.group(1) if m else msg_of(sig)[:60]] += 1
    elif fam == "NOSUCHMETHOD":
        m = re.search(r"No such method[^\n]*", sig, re.I)
        m2 = re.search(r"L[\w/$]+;\.(\S+)\(", sig)
        nsm[(m.group(0)[:70] if m else (m2.group(1) if m2 else msg_of(sig)[:60]))] += 1
    elif fam in ("NPE-FAMILY", "SHAREDPREFS", "THREAD-UEH-HANDLER", "FRAGMENT-HOST"):
        ms = msg_of(sig)
        # normalize: strip quoted content variety, keep the API anchor
        anchor = re.sub(r"'[^']*'", "'X'", ms)[:110]
        npe_msgs[anchor] += 1

print("=== CLASSNOTFOUND missing classes (17 titles) ===")
for k, c in cnf.most_common(25):
    print(f"  {c:3d}  {k}")
print("\n=== NOSUCHMETHOD (13 titles) ===")
for k, c in nsm.most_common(25):
    print(f"  {c:3d}  {k}")
print("\n=== NPE message anchors (31+5+4+1 titles) ===")
for k, c in npe_msgs.most_common(30):
    print(f"  {c:3d}  {k}")
