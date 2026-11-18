#!/usr/bin/env python3
"""W9.2 state verification: branch/remote/compare/existing-PRs/issue state. Token never printed."""
import json, subprocess, re

cfg = subprocess.run(["git", "config", "--list"], capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
tok = re.search(r"github_pat_[A-Za-z0-9_]*", cfg).group(0)
H = ["-H", f"Authorization: Bearer {tok}"]
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"

def api(path):
    out = subprocess.run(["curl", "-s", *H, f"{BASE}{path}"], capture_output=True, text=True).stdout
    return json.loads(out)

R = {}
# local + remote branch state
for cmd in [("HEAD", "git rev-parse HEAD"),
            ("branch", "git branch --show-current"),
            ("clean_head", "git rev-parse wave9/dev-so-clean"),
            ("remote_head", "git ls-remote origin refs/heads/wave9/dev-so-clean"),
            ("remote_main", "git ls-remote origin refs/heads/main")]:
    r = subprocess.run(cmd[1].split(), capture_output=True, text=True, cwd="/home/z/my-project")
    R[cmd[0]] = r.stdout.strip().split("\t")[0] if "\t" in r.stdout else r.stdout.strip()
print(json.dumps(R, indent=1))

# authoritative compare (actual GitHub result)
cmp_ = api("/compare/main...wave9/dev-so-clean")
C = {"status": cmp_.get("status"), "ahead_by": cmp_.get("ahead_by"), "behind_by": cmp_.get("behind_by"),
     "files": len(cmp_.get("files", [])), "merge_base": (cmp_.get("merge_base_commit") or {}).get("sha", "")[:12],
     "commits": [c["sha"][:12] for c in cmp_.get("commits", [])]}
print("COMPARE:", json.dumps(C, indent=1))

# existing PRs (all open + any from this branch)
prs = api("/pulls?state=open&per_page=50")
pl = [{"number": p["number"], "title": p["title"][:60], "head": p["head"]["ref"], "base": p["base"]["ref"],
       "url": p["html_url"], "state": p["state"], "mergeable_state": p.get("mergeable_state")} for p in prs]
print("OPEN_PRS:", json.dumps(pl, indent=1))

# issue #612 state
iss = api("/issues/612")
I = {"state": iss.get("state"), "title": iss.get("title", "")[:60], "comments": iss.get("comments")}
print("ISSUE612:", json.dumps(I, indent=1))

json.dump({"refs": R, "compare": C, "open_prs": pl, "issue612": I},
          open("/tmp/w92_state.json", "w"), indent=1)
print("STATE saved")
