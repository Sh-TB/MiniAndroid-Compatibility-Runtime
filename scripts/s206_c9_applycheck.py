#!/usr/bin/env python3
"""S206 — C9 S198 rebased phase-3 parts 1-4: extract the diff fences from the
comment markdown files, reassemble the full patch, git apply --check on the
current tree (HEAD 45d019fc = 0979678e + .gitignore)."""
import re, subprocess, sys
from pathlib import Path

S = Path('/home/z/my-project/evidence/s206')
PATCH = S / 'c9_s198_rebased_FULL.patch'

parts = ['c9_s198_patch_p1.md', 'c9_s198_patch_p2.md', 'c9_s198_patch_p3.md', 'c9_s198_patch_p4.md']
chunks = []
for p in parts:
    txt = (S / p).read_text()
    fences = re.findall(r"```diff\n(.*?)```", txt, re.S)
    if not fences:
        sys.exit(f"NO diff fence in {p}")
    chunks.append(fences[0].rstrip("\n"))
    print(f"{p}: fence {len(fences[0])} chars")

full = "\n".join(chunks) + "\n"
PATCH.write_text(full)
print(f"full patch: {len(full)} chars -> {PATCH}")

r = subprocess.run(["git", "apply", "--check", str(PATCH)],
                   cwd="/home/z/my-project", capture_output=True, text=True)
print("git apply --check rc =", r.returncode)
if r.stdout.strip(): print("stdout:", r.stdout[:2000])
if r.stderr.strip(): print("stderr:", r.stderr[:3000])
