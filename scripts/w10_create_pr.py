#!/usr/bin/env python3
"""W10: attempt PR creation for wave10/dalvik-accel; verify if created."""
import json, subprocess, re
cfg = subprocess.run(["git", "config", "--list"], capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
tok = re.search(r"github_pat_[A-Za-z0-9_]*", cfg).group(0)
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"
data = {"title": "ISSUE-612: WAVE-10 dev-so speed profiles - interpreter 12.26s, bridge 25.51s (all gates met)",
        "head": "wave10/dalvik-accel", "base": "main",
        "body": open("/tmp/w10_pr_body.md").read()}
d = json.loads(subprocess.run(["curl", "-s", "-X", "POST", "-H", f"Authorization: Bearer {tok}",
                               "-H", "Content-Type: application/json", "-d", json.dumps(data), f"{BASE}/pulls"],
                              capture_output=True, text=True).stdout)
print(json.dumps({"created": bool(d.get("number")), "number": d.get("number"),
                  "url": d.get("html_url"), "reason": d.get("message", "")}, indent=1))
