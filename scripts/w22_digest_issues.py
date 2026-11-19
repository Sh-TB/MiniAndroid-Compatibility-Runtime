#!/usr/bin/env python3
"""w22_digest_issues.py — digest fetched issue JSONs into:
  1. issues_inventory.tsv (all 629 items, one line each)
  2. target_digest.md — full bodies + comments of the 9 mission issues + PR 626
"""
import json
import os
import re

OUT = "/home/z/my-project/evidence/w22/issues_raw"
INV = "/home/z/my-project/evidence/w22/issues_inventory.tsv"
DIG = "/home/z/my-project/evidence/w22/target_digest.md"
TARGETS = [573, 586, 597, 606, 607, 612, 620, 627, 628, 626]

items = []
for fn in sorted(os.listdir(OUT)):
    if fn.startswith("page_") and fn.endswith(".json"):
        with open(os.path.join(OUT, fn)) as f:
            items.extend(json.load(f))

with open(INV, "w") as f:
    f.write("number\ttype\tstate\tauthor\tcreated\tcomments\ttitle\n")
    for it in sorted(items, key=lambda x: x["number"]):
        kind = "PR" if "pull_request" in it else "I"
        f.write("%d\t%s\t%s\t%s\t%s\t%d\t%s\n" % (
            it["number"], kind, it["state"],
            it.get("user", {}).get("login", "?"),
            it.get("created_at", ""), it.get("comments", 0),
            it.get("title", "").replace("\t", " ")[:110]))
print("inventory rows:", len(items))


def clean(t):
    if not t:
        return ""
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    return t.strip()


with open(DIG, "w") as f:
    for n in TARGETS:
        with open("%s/item_%d.json" % (OUT, n)) as fh:
            it = json.load(fh)
        f.write("\n\n===== %s #%d | %s | state=%s | author=%s | created=%s =====\n" % (
            "PR" if "pull_request" in it else "ISSUE", n, it.get("title", ""),
            it.get("state"), it.get("user", {}).get("login"),
            it.get("created_at")))
        body = clean(it.get("body", ""))
        f.write(body[:18000] + "\n")
        cfn = "%s/comments_%d.json" % (OUT, n)
        if os.path.exists(cfn):
            with open(cfn) as fh:
                cs = json.load(fh)
            for c in cs:
                f.write("\n--- comment %s by %s at %s ---\n" % (
                    c.get("id"), c.get("user", {}).get("login"),
                    c.get("created_at")))
                f.write(clean(c.get("body", ""))[:9000] + "\n")
print("digest written")
