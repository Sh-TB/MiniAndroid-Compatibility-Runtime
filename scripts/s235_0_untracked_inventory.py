#!/usr/bin/env python3
"""S235-0: append the local-only-artifacts ignore section to .gitignore (v2).

Source of truth = the CURRENT untracked inventory (git ls-files --others),
not the sweep commit: the sandbox recycle restored a superset of what the
boundary sweep captured. Tracked files are never untracked by gitignore, so
already-promoted curated evidence stays tracked.
"""
import subprocess
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
GITIGNORE = BASE / ".gitignore"
PRE = "cfba2f41"  # last deliberate commit (S234-3) == origin/main

def sh(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True, cwd=BASE,
                          check=True).stdout

untracked = [l for l in sh("git", "ls-files", "--others",
                           "--exclude-standard").splitlines() if l.strip()]
print(f"untracked now: {len(untracked)}")

# group: (top-level, second-level-or-None)
groups = Counter()
loose = []
for p in untracked:
    parts = p.split("/")
    if len(parts) == 1:
        loose.append(p)
    elif parts[0] in ("evidence", "docs"):
        groups[(parts[0], "/".join(parts[:3] if parts[0] == "docs"
                                 else parts[:2]))] += 1
    else:
        groups[(parts[0], None)] += 1

print("== loose root files ==")
for p in sorted(loose):
    print("  ", p)
print("== groups ==")
for (top, sub), n in sorted(groups.items()):
    print(f"  {top}/{sub or ''}: {n}")
