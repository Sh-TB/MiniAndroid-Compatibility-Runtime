#!/usr/bin/env python3
"""w22_extract_patches.py — extract inline diff/patch content from fetched
issue comments into evidence/w22/patches/, and list attachment URLs."""
import json
import os
import re

RAW = "/home/z/my-project/evidence/w22/issues_raw"
OUT = "/home/z/my-project/evidence/w22/patches"
os.makedirs(OUT, exist_ok=True)


def clean(t):
    t = re.sub(r"<!--.*?-->", "", t or "", flags=re.S)
    return t


for n in (573, 586, 597, 606, 607, 612, 620, 627, 628):
    fn = "%s/comments_%d.json" % (RAW, n)
    if not os.path.exists(fn):
        continue
    cs = json.load(open(fn))
    for c in cs:
        body = clean(c.get("body", ""))
        # attachment URLs
        urls = re.findall(r"https://github\.com/user-attachments/[^\s\)\"]+", body)
        for u in urls:
            print("ATTACH %d c%s %s" % (n, c["id"], u))
        # fenced diffs
        blocks = re.findall(r"```(?:diff|patch)?\n(.*?)```", body, flags=re.S)
        did = 0
        for b in blocks:
            if re.search(r"^diff --git|^--- a/|^\+\+\+ b/|^@@ ", b, flags=re.M):
                did += 1
                path = "%s/patch_i%d_c%s_%d.diff" % (OUT, n, c["id"], did)
                with open(path, "w") as f:
                    f.write(b if b.endswith("\n") else b + "\n")
                files = re.findall(r"^diff --git a/(\S+)", b, flags=re.M)
                print("PATCH %d c%s -> %s  files: %s" % (
                    n, c["id"], os.path.basename(path), files[:6]))
        # whole-comment-as-patch (S226 style)
        if "diff --git" not in body and re.search(r"^--- a/|^Index:|^\*\*\* ", body, flags=re.M):
            path = "%s/patch_i%d_c%s_unfenced.diff" % (OUT, n, c["id"])
            with open(path, "w") as f:
                f.write(body + "\n")
            print("PATCH-UNFENCED %d c%s" % (n, c["id"]))
print("DONE")
