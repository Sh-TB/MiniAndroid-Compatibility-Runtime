#!/usr/bin/env python3
"""FINAL Phase 1: merge PR #625 (merge commit), verify reachability. Never force/reset."""
import json, subprocess, re

cwd = "/home/z/my-project"
cfg = subprocess.run(["git", "config", "--list"], capture_output=True, text=True, cwd=cwd).stdout
tok = re.search(r"github_pat_[A-Za-z0-9_]*", cfg).group(0)
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"
r = subprocess.run(["curl", "-s", "-X", "PUT", "-H", f"Authorization: Bearer {tok}",
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps({"merge_method": "merge"}), f"{BASE}/pulls/625/merge"],
                   capture_output=True, text=True).stdout
out = json.loads(r)
print("MERGE 625:", json.dumps({"merged": out.get("merged"), "sha": (out.get("sha") or "")[:12],
                                "message": out.get("message")}))
json.dump(out, open("/tmp/f_merge625.json", "w"))
if out.get("merged"):
    subprocess.run(["git", "fetch", "origin"], capture_output=True, cwd=cwd)
    main = subprocess.run(["git", "rev-parse", "origin/main"], capture_output=True, text=True, cwd=cwd).stdout.strip()
    anc = subprocess.run(["git", "merge-base", "--is-ancestor", "1e5c8fb9", "origin/main"],
                         capture_output=True, cwd=cwd).returncode == 0
    anc2 = subprocess.run(["git", "merge-base", "--is-ancestor", out["sha"], "origin/main"],
                          capture_output=True, cwd=cwd).returncode == 0
    print("origin/main:", main[:12], "| wave9(1e5c8fb9) reachable:", anc, "| merge commit reachable:", anc2)
