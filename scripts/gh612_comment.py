#!/usr/bin/env python3
"""Post a checkpoint comment to Issue #612. Body from a file argument."""
import json, subprocess, sys, re
cfg = subprocess.run(["git", "config", "--list"], capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
tok = re.search(r"github_pat_[A-Za-z0-9_]*", cfg).group(0)
body = open(sys.argv[1]).read()
url = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/612/comments"
out = subprocess.run(["curl", "-s", "-X", "POST", "-H", f"Authorization: Bearer {tok}",
     "-H", "Content-Type: application/json", "-d", json.dumps({"body": body}), url],
    capture_output=True, text=True).stdout
print(json.loads(out).get("html_url", "ERR"))
