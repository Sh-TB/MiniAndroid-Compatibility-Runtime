#!/usr/bin/env python3
"""W12 Phase 0: remote + local state verification."""
import json, subprocess, re, os
cwd = "/home/z/my-project"
cfg = subprocess.run(["git", "config", "--list"], capture_output=True, text=True, cwd=cwd).stdout
tok = re.search(r"github_pat_[A-Za-z0-9_]*", cfg).group(0)
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"
H = ["-H", f"Authorization: Bearer {tok}"]
def api(p):
    import urllib.request
    r = urllib.request.Request(f"{BASE}{p}", headers={"Authorization": f"Bearer {tok}"})
    return json.load(urllib.request.urlopen(r))
subprocess.run(["git", "fetch", "origin"], capture_output=True, cwd=cwd)
out = {}
out["local_branch"] = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=cwd).stdout.strip()
out["local_head"] = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=cwd).stdout.strip()[:12]
out["dirty"] = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=cwd).stdout.strip().splitlines()
out["remote_wave10"] = subprocess.run(["git", "ls-remote", "origin", "refs/heads/wave10/dalvik-accel"], capture_output=True, text=True, cwd=cwd).stdout.split()[0][:12]
out["remote_main"] = subprocess.run(["git", "ls-remote", "origin", "refs/heads/main"], capture_output=True, text=True, cwd=cwd).stdout.split()[0][:12]
pr = api("/pulls/626")
out["pr626"] = {"state": pr.get("state"), "merged": pr.get("merged"),
                "base": (pr.get("base") or {}).get("ref"), "head": (pr.get("head") or {}).get("ref"),
                "head_sha": ((pr.get("head") or {}).get("sha") or "")[:12],
                "mergeable": pr.get("mergeable"), "mergeable_state": pr.get("mergeable_state")}
try:
    iss = api("/issues/612")
    out["issue612"] = {"state": iss.get("state"), "comments": iss.get("comments")}
except Exception as e:
    out["issue612"] = str(e)
# ancestry: are the W11 commits on the remote branch?
for c, lab in [("b5799977", "w11-doc"), ("d14582b3", "w11-fixes")]:
    r = subprocess.run(["git", "merge-base", "--is-ancestor", c, "origin/wave10/dalvik-accel"], capture_output=True, cwd=cwd)
    out[f"{lab}_on_remote_branch"] = (r.returncode == 0)
# F-709/710/711 presence in the checked-out tree
checks = {
 "F709_getfd_guard": "F-NEW-709" in open("miniandroid/src/dex/dalvik_bridge.cpp").read(),
 "F709_fd_map": "fd_to_stream_" in open("miniandroid/src/dex/dalvik_engine.h").read(),
 "F710_invoke_byval": "BY VALUE (F-NEW-710)" in open("miniandroid/src/dex/dalvik_engine_invoke.cpp").read(),
 "F710_core_byval": "BY VALUE (F-NEW-710)" in open("miniandroid/src/dex/dalvik_engine_core.cpp").read(),
 "F711_probe_gate": "F-NEW-711" in open("miniandroid/src/runtime/execution_engine.cpp").read(),
 "F709_regression_test": os.path.exists("miniandroid/tests/f709_filedescriptor_law_test.cpp"),
 "eng_doc": os.path.exists("miniandroid/docs/dev-so-architecture.md"),
 "evidence_w11": os.path.exists("miniandroid/evidence/wave11/apk_campaign.json"),
}
out["fix_presence"] = checks
print(json.dumps(out, indent=1))
json.dump(out, open("/tmp/w12_phase0.json", "w"), indent=1)
