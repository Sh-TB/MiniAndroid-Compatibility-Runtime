#!/usr/bin/env python3
"""w22_reconstruct.py — reconstruct the RC-1/#607 new files from the recovered
patch into the working tree (renamed where the s-number collides):
  miniandroid/VERSION                                  (verbatim)
  miniandroid/scripts/generate_version_header.py       (verbatim)
  miniandroid/tests/s254_version_identity_law_test.cpp (from s249, renamed)
"""
import re

PATCH = "/home/z/my-project/evidence/w22/patches/patch_i607_c6989841969_1.diff"
ROOT = "/home/z/my-project"

txt = open(PATCH).read()
files = {}
for f in re.split(r"(?m)^diff --git ", txt):
    m = re.match(r"a/(\S+)", f)
    if not m:
        continue
    files[m.group(1)] = f


def added_lines(section):
    body = section.split("\n", 2)[2]
    out = []
    for l in body.splitlines():
        if l.startswith("+") and not l.startswith("+++"):
            out.append(l[1:])
        elif l.startswith("-") or l.startswith("@@"):
            continue
    return out


targets = [
    ("miniandroid/VERSION", "miniandroid/VERSION", False),
    ("miniandroid/scripts/generate_version_header.py",
     "miniandroid/scripts/generate_version_header.py", False),
    ("miniandroid/tests/s249_version_identity_law_test.cpp",
     "miniandroid/tests/s254_version_identity_law_test.cpp", True),
]
for src, dst, rename in targets:
    sec = files[src]
    lines = added_lines(sec)
    content = "\n".join(lines) + "\n"
    if rename:
        content = content.replace(
            "s249_version_identity_law_test", "s254_version_identity_law_test")
        content = content.replace(
            "// s254_version_identity_law_test — ISSUE-607 item 8 (P2).",
            "// s254_version_identity_law_test — ISSUE-607 item 8 (P2).\n"
            "// W22 integration: renamed from the recovered #607 patch s249\n"
            "// (main's s249/s248 names are owned by the W20-K contract tests;\n"
            "// provenance: #607 issuecomment patch, base 9dafaadd).")
    with open("%s/%s" % (ROOT, dst), "w") as f:
        f.write(content)
    print("WROTE %s (%d lines)" % (dst, len(lines)))
print("DONE")
