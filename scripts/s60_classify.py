#!/usr/bin/env python3
"""s60_classify.py — classify all open issues for the reconciliation: ladder completeness,
closure candidates, supersession candidates. Outputs run/s60/classification.json + a TSV digest."""
import json
import re

SRC = "/home/z/my-project/run/s60/issues_all.json"
OUTJ = "/home/z/my-project/run/s60/classification.json"
OUTT = "/home/z/my-project/run/s60/classification.tsv"

issues = json.load(open(SRC))

rows = []
for it in issues:
    body = it["body"] or ""
    checked = len(re.findall(r"(?m)^\s*[-*+]\s+\[x\]", body, re.I))
    unchecked = len(re.findall(r"(?m)^\s*[-*+]\s+\[x?x?\]\s", body))  # placeholder
    unchecked = len(re.findall(r"(?m)^\s*[-*+]\s+\[ \]", body))
    labels = it["labels"]
    is_perapp = any(l.startswith(("state-",)) for l in labels) or bool(re.match(r"\[EXEC\]", it["title"]))
    # group assignment from the S59 matrix conventions
    if re.search(r"MICRO-GAP", it["title"]):
        grp = "micro-gap"
    elif re.match(r"\[EXEC\]", it["title"]) or "CAMPAIGN" in body.upper()[:200]:
        grp = "per-app"
    elif re.search(r"TELEGRAM|KNOWLEDGE TRANSFER", it["title"], re.I):
        grp = "telegram"
    elif re.search(r"ROADMAP", it["title"], re.I):
        grp = "roadmap"
    elif re.search(r"CONT-\d+|WAVE", it["title"], re.I):
        grp = "wave-exec"
    else:
        grp = "work"
    rows.append({
        "number": it["number"], "title": it["title"][:90], "group": grp,
        "labels": ",".join(labels), "checked": checked, "unchecked": unchecked,
        "updated": it["updated"], "comments": it["comments"],
        "closure_candidate": (checked > 0 and unchecked == 0),
    })

json.dump(rows, open(OUTJ, "w"), indent=1)
with open(OUTT, "w") as f:
    f.write("number\tgroup\tchecked\tunchecked\tcandidate\tcomments\ttitle\n")
    for r in sorted(rows, key=lambda x: (-x["closure_candidate"], x["number"])):
        f.write(f"{r['number']}\t{r['group']}\t{r['checked']}\t{r['unchecked']}\t"
                f"{int(r['closure_candidate'])}\t{r['comments']}\t{r['title']}\n")

cand = [r for r in rows if r["closure_candidate"]]
from collections import Counter
print("groups:", dict(Counter(r["group"] for r in rows)))
print("closure candidates (all-checked ladders):", len(cand))
for r in sorted(cand, key=lambda x: x["number"]):
    print(f"  #{r['number']} [{r['group']}] {r['title'][:70]}")
