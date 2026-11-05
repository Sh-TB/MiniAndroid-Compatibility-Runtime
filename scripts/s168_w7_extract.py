#!/usr/bin/env python3
"""S168: extract w7_laws.patch from the #518 comment (fence-stripped),
sha16 check vs claim ea55443a44263012, then git apply --check on HEAD."""
import hashlib
import re
import subprocess
from pathlib import Path

BASE = Path("/home/z/my-project")
SRC = BASE / "evidence/s168_w7/w7_comment_6638731163.md"
OUT = BASE / "evidence/s168_w7/w7_laws.patch"
CLAIM = "ea55443a44263012"

body = SRC.read_text()
# strip the ```diff fence: keep lines between the opening ```diff and closing ```
lines = body.splitlines()
start = next(i for i, l in enumerate(lines) if l.strip().startswith("```diff"))
end = next(i for i in range(start + 1, len(lines))
           if lines[i].strip() == "```")
patch_lines = lines[start + 1:end]
patch = "\n".join(patch_lines) + "\n"
OUT.write_text(patch)
n = len(patch_lines)
sha16 = hashlib.sha256(patch.encode()).hexdigest()[:16]
print(f"extracted: lines={n} chars={len(patch)} sha16={sha16}")
print(f"claim    : lines=137 sha16={CLAIM}")
print("SHA MATCH:", sha16 == CLAIM, "| LINES MATCH:", n == 137)

# structure check
files = [l for l in patch_lines if l.startswith("--- a/")]
print("files touched:", files)

r = subprocess.run(["git", "apply", "--check", str(OUT)],
                   cwd=BASE, capture_output=True, text=True)
print("git apply --check:", "CLEAN" if r.returncode == 0 else "FAIL")
print(r.stdout or "")
print(r.stderr or "")
