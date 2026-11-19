#!/usr/bin/env python3
"""W10.1 Phase 0: verify GitHub state - SHAs, existing PRs, issue #612. Token never printed."""
import json, subprocess, re

cfg = subprocess.run(["git", "config", "--list"], capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
tok = re.search(r"github_pat_[A-Za-z0-9_]*", cfg).group(0)
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"
H = ["-H", f"Authorization: Bearer {tok}"]

def api(path):
    return json.loads(subprocess.run(["curl", "-s", *H, f"{BASE}{path}"],
                                     capture_output=True, text=True).stdout)

R = {}
for name, ref in [("main", "refs/heads/main"), ("wave9", "refs/heads/wave9/dev-so-clean"),
                  ("wave10", "refs/heads/wave10/dalvik-accel")]:
    out = subprocess.run(["git", "ls-remote", "origin", ref], capture_output=True,
                         text=True, cwd="/home/z/my-project").stdout.strip()
    R[name] = out.split("\t")[0] if out else "MISSING"
print("REFS:", json.dumps(R, indent=1))

prs = api("/pulls?state=all&per_page=30")
pl = [{"number": p["number"], "state": p["state"], "merged": p.get("merged", False),
       "title": p["title"][:60], "base": p["base"]["ref"], "head": p["head"]["ref"]} for p in prs]
print("PRS(all):", json.dumps(pl, indent=1))

iss = api("/issues/612")
print("ISSUE612:", json.dumps({"state": iss.get("state"), "comments": iss.get("comments")}, indent=1))
json.dump({"refs": R, "prs": pl, "issue": {"state": iss.get("state"), "comments": iss.get("comments")}},
          open("/tmp/w101_state.json", "w"), indent=1)
