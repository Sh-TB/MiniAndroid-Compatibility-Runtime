#!/usr/bin/env python3
"""FINAL Phase 0: full remote state - refs, PR #625/#626, issue #612, checks, protection, tags."""
import json, subprocess, re

cwd = "/home/z/my-project"
cfg = subprocess.run(["git", "config", "--list"], capture_output=True, text=True, cwd=cwd).stdout
tok = re.search(r"github_pat_[A-Za-z0-9_]*", cfg).group(0)
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"
H = ["-H", f"Authorization: Bearer {tok}"]

def api(p):
    r = subprocess.run(["curl", "-s", *H, f"{BASE}{p}"], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"_raw": r.stdout[:300]}

refs = {}
for name, ref in [("main", "refs/heads/main"), ("wave9", "refs/heads/wave9/dev-so-clean"),
                  ("wave10", "refs/heads/wave10/dalvik-accel")]:
    out = subprocess.run(["git", "ls-remote", "origin", ref], capture_output=True, text=True, cwd=cwd).stdout.strip()
    refs[name] = out.split("\t")[0] if out else "MISSING"

repo = api("")
pr = {n: api(f"/pulls/{n}") for n in (625, 626)}
iss = api("/issues/612")

def psumm(n, p):
    return {"number": n, "state": p.get("state"), "merged": p.get("merged"),
            "merge_commit_sha": (p.get("merge_commit_sha") or "")[:12], "draft": p.get("draft"),
            "base": (p.get("base") or {}).get("ref"), "head": (p.get("head") or {}).get("ref"),
            "head_sha": ((p.get("head") or {}).get("sha") or "")[:12],
            "mergeable": p.get("mergeable"), "mergeable_state": p.get("mergeable_state"),
            "changed_files": p.get("changed_files"), "additions": p.get("additions"),
            "deletions": p.get("deletions"), "title": (p.get("title") or "")[:70],
            "merge_method_allowed": {k: repo.get(k) for k in
                                     ("allow_merge_commit", "allow_squash_merge", "allow_rebase_merge")}}

files = {n: [{"f": x["filename"], "a": x["additions"]} for x in api(f"/pulls/{n}/files?per_page=100")]
         for n in (625, 626)}

checks = {}
for lab, p in [("pr625", pr[625]), ("pr626", pr[626])]:
    sha = (p.get("head") or {}).get("sha")
    if sha:
        cr = api(f"/commits/{sha}/check-runs")
        st = api(f"/commits/{sha}/status")
        checks[lab] = {"sha": sha[:12], "check_runs": cr.get("total_count", 0),
                       "check_names": [c.get("name") for c in cr.get("check_runs", [])][:8],
                       "combined": st.get("state", "none"), "statuses": len(st.get("statuses") or [])}

reviews = {n: [{"user": r["user"]["login"], "state": r["state"]} for r in api(f"/pulls/{n}/reviews")]
           for n in (625, 626)}
prot = api("/branches/main/protection")
tags = [t["name"] for t in api("/tags?per_page=100")]
reach = bool(api("/commits/96cd29e2").get("sha"))

out = {"refs": refs, "repo_default_branch": repo.get("default_branch"),
       "pr625": psumm(625, pr[625]), "pr626": psumm(626, pr[626]),
       "pr625_files": files[625], "pr626_files": files[626],
       "checks": checks, "reviews": reviews,
       "protection": {"raw_error": prot.get("message"),
                      "required_reviews": (prot.get("required_pull_request_reviews") or {}).get("required_approving_review_count")},
       "tags": tags, "c96cd29e2_remote": reach,
       "issue612": {"state": iss.get("state"), "comments": iss.get("comments")},
       "local": {"head": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=cwd).stdout.strip()[:12],
                 "branch": subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=cwd).stdout.strip(),
                 "dirty": subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=cwd).stdout.count("\n")}}
json.dump(out, open("/tmp/f_phase0.json", "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ("pr625_files", "pr626_files")}, indent=1))
fa = sorted(files[625], key=lambda x: -x["a"])[:12]
print("PR625 top-addition files:", json.dumps(fa, indent=0))
print("PR626 file count:", len(files[626]), "| PR625 file count:", len(files[625]))
