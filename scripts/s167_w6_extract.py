#!/usr/bin/env python3
"""S167: extract W6 patch payloads from #517 comments (evidence/s167_w6/)."""
import hashlib
import json
import os

SRC = "/tmp/i517_comments.json"
OUT = "/home/z/my-project/evidence/s167_w6"

os.makedirs(OUT, exist_ok=True)
comments = json.load(open(SRC))
for c in comments:
    body = c["body"]
    if "diff --git" not in body and "--- a/" not in body:
        print(f"comment {c['id']}: no diff payload, skip")
        continue
    # header = prose before first diff --git (claims block)
    idx = body.find("diff --git")
    header = body[:idx] if idx >= 0 else body
    fname = os.path.join(OUT, f"w6_comment_{c['id']}.patch")
    with open(fname, "w") as f:
        f.write(body)
    nlines = body.count("\n") + (0 if body.endswith("\n") else 1)
    sha16 = hashlib.sha256(body.encode()).hexdigest()[:16]
    print(f"comment {c['id']}: -> {fname}")
    print(f"  chars={len(body)} lines~={nlines} sha16={sha16}")
    hdr = header.strip().splitlines()
    print(f"  header ({len(hdr)} lines):")
    for hl in hdr[:25]:
        print(f"    | {hl[:150]}")
    # diff targets
    targets = [l for l in body.splitlines() if l.startswith("diff --git")]
    print(f"  files touched ({len(targets)}):")
    for t in targets:
        print(f"    {t[:160]}")
    print()
