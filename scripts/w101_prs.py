#!/usr/bin/env python3
"""W10.1 Phase 4: attempt stacked PRs - PR1 main<-wave9, PR2 wave9<-wave10."""
import json, subprocess, re
cfg = subprocess.run(["git", "config", "--list"], capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
tok = re.search(r"github_pat_[A-Za-z0-9_]*", cfg).group(0)
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"
BODIES = {"pr1": open("/home/z/my-project/download/wave9_pr_body_clean.md").read(),
          "pr2": open("/home/z/my-project/download/wave10_pr_body_stacked.md").read()}
PR1 = {"title": "ISSUE-612: Add opt-in shared Dalvik .so development build path",
       "head": "wave9/dev-so-clean", "base": "main", "body": BODIES["pr1"]}
PR2 = {"title": "ISSUE-612: WAVE-10 dev-so speed profiles - interpreter 12.26s, bridge 25.51s (all gates met)",
       "head": "wave10/dalvik-accel", "base": "wave9/dev-so-clean", "body": BODIES["pr2"]}
for name, data in [("PR1", PR1), ("PR2", PR2)]:
    d = json.loads(subprocess.run(["curl", "-s", "-X", "POST", "-H", f"Authorization: Bearer {tok}",
        "-H", "Content-Type: application/json", "-d", json.dumps(data), f"{BASE}/pulls"],
        capture_output=True, text=True).stdout)
    print(name, json.dumps({"created": bool(d.get("number")), "number": d.get("number"),
                            "url": d.get("html_url"), "reason": d.get("message", "")}))
