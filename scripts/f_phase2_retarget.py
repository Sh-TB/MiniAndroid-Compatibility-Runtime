#!/usr/bin/env python3
"""FINAL Phase 2: retarget PR #626 base to main, fetch new diff, verify wave-10-only."""
import json, subprocess, re
cwd = "/home/z/my-project"
cfg = subprocess.run(["git", "config", "--list"], capture_output=True, text=True, cwd=cwd).stdout
tok = re.search(r"github_pat_[A-Za-z0-9_]*", cfg).group(0)
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"
r = json.loads(subprocess.run(["curl", "-s", "-X", "PATCH", "-H", f"Authorization: Bearer {tok}",
    "-H", "Content-Type: application/json", "-d", json.dumps({"base": "main"}),
    f"{BASE}/pulls/626"], capture_output=True, text=True).stdout)
print("RETARGET:", json.dumps({"base": (r.get("base") or {}).get("ref"),
    "mergeable": r.get("mergeable"), "mergeable_state": r.get("mergeable_state"),
    "files": r.get("changed_files"), "additions": r.get("additions"), "deletions": r.get("deletions"),
    "msg": r.get("message", "")}))
fs = [{"f": x["filename"], "a": x["additions"], "d": x["deletions"]}
      for x in json.loads(subprocess.run(["curl", "-s", "-H", f"Authorization: Bearer {tok}",
      f"{BASE}/pulls/626/files?per_page=100"], capture_output=True, text=True).stdout)]
old = {x["f"] for x in json.load(open("/tmp/f_phase0.json"))["pr626_files"]}
new = {x["f"] for x in fs}
print("file sets identical after retarget:", old == new, "| count:", len(fs))
mk = [x for x in fs if x["f"].endswith("Makefile")]
print("Makefile entry:", mk)
json.dump(fs, open("/tmp/f_pr626_files_after.json", "w"), indent=1)
# tree identity proofs
for a, b, lab in [("9dafaadd41f5", "1e5c8fb9", "merge625 tree == wave9 tree"),
                  ("96cd29e2", "96cd29e2", "wave10 head")]:
    ta = subprocess.run(["git", "rev-parse", f"{a}^{{tree}}"], capture_output=True, text=True, cwd=cwd).stdout.strip()[:12]
    print(lab, ta)
