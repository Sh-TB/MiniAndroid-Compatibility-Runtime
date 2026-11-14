#!/usr/bin/env python3
"""S235-0 (finisher): extend the boundary-sweep ignore section with the rules
for every remaining untracked path group: the 60 historical evidence dirs,
8 docs/evidence subdirs, and the loose build byproduct. Idempotent.
"""
import subprocess
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
GITIGNORE = BASE / ".gitignore"

def sh(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True, cwd=BASE,
                          check=True).stdout

untracked = [l for l in sh("git", "ls-files", "--others",
                           "--exclude-standard").splitlines() if l.strip()]
rules, other = set(), []
for p in untracked:
    if p == "scripts/s235_0_gitignore_fix.py" or \
       p == "scripts/s235_0_untracked_inventory.py" or \
       p == ".gitignore":
        other.append(p)  # committed deliberately, not ignored
        continue
    parts = p.split("/")
    if parts[0] == "evidence":
        rules.add(f"/evidence/{parts[1]}/")
    elif parts[0] == "docs" and len(parts) >= 3:
        rules.add(f"/docs/evidence/{parts[2]}/")
    elif parts[0] == "miniandroid" and len(parts) == 2:
        rules.add("/" + p)  # loose build byproducts at miniandroid/ top level
    else:
        rules.add("/" + p)

cur = GITIGNORE.read_text()
new = sorted(r for r in rules if r not in cur.splitlines())
marker = "# historical pre-S230 evidence dirs carrying untracked run artifacts"
addition = ""
if new:
    addition = "\n# --- inventory-completion pass (v2): every remaining untracked group ---\n"
    addition += "".join(r + "\n" for r in new)
    GITIGNORE.write_text(cur.rstrip("\n") + "\n" + addition)
print(f"added {len(new)} rules; deliberate (not ignored): {sorted(set(other))}")
left = sh("git", "ls-files", "--others", "--exclude-standard").splitlines()
print(f"untracked after ignore: {len(left)}")
for l in left:
    print("  remaining:", l)
