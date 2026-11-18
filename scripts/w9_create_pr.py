#!/usr/bin/env python3
"""Create the WAVE-9.1 clean PR via GitHub API. Token read from git config, never printed."""
import json, subprocess, re
cfg = subprocess.run(["git", "config", "--list"], capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
tok = re.search(r"github_pat_[A-Za-z0-9_]*", cfg).group(0)
url = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/pulls"
body = open("/home/z/my-project/download/wave9_pr_body_clean.md").read()
data = {"title": "WAVE-9 (clean): opt-in shared-library dev path on top of remote main - minimal 2-commit patch, full re-verification",
        "head": "wave9/dev-so-clean", "base": "main", "body": body}
out = subprocess.run(["curl", "-s", "-X", "POST", "-H", f"Authorization: Bearer {tok}",
                      "-H", "Content-Type: application/json", "-d", json.dumps(data), url],
                     capture_output=True, text=True).stdout
d = json.loads(out)
print(d.get("html_url") or d.get("message") or "ERR")
