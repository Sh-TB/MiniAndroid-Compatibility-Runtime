#!/usr/bin/env python3
"""S177 intake step 2: git apply --check (+real apply) of the extracted
coder patches on their declared base trees via throwaway worktrees."""
import subprocess, os, sys, json

OUT = "evidence/s177_intake"
WT = "/tmp/s177_wt"
report = {}

def git(*args, cwd=None):
    r = subprocess.run(["git"] + list(args), capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def wt_at(commit, name):
    p = f"{WT}/{name}"
    if os.path.exists(p):
        subprocess.run(["git", "worktree", "remove", "--force", p], capture_output=True)
    rc, o, e = git("worktree", "add", "--detach", p, commit)
    return p if rc == 0 else None

def check_apply(patch, cwd, label):
    rc, o, e = git("apply", "--check", patch, cwd=cwd)
    ok = rc == 0
    print(f"[{label}] git apply --check: {'CLEAN' if ok else 'FAIL'}")
    if not ok:
        print("   stderr:", (e or o)[:500])
    return ok

def apply(patch, cwd, label):
    rc, o, e = git("apply", patch, cwd=cwd)
    print(f"[{label}] git apply: {'OK' if rc == 0 else 'FAIL'}")
    if rc != 0:
        print("   stderr:", (e or o)[:500])
    return rc == 0

os.makedirs(WT, exist_ok=True)

# ── C7: 439b0a3d + w1w2 → w3 ─────────────────────────────────────────────
c7 = wt_at("439b0a3d", "c7")
if c7:
    ok1 = check_apply(f"/home/z/my-project/{OUT}/c7_w1w2_on_s170.patch", c7, "C7 w1w2 on 439b0a3d")
    if ok1 and apply(f"/home/z/my-project/{OUT}/c7_w1w2_on_s170.patch", c7, "C7 w1w2 apply"):
        ok2 = check_apply(f"/home/z/my-project/{OUT}/c7_w3_on_w2.patch", c7, "C7 w3 on w1w2-tree")
        report["c7_w1w2_apply"] = "CLEAN+APPLIED"
        report["c7_w3_applycheck_on_w2tree"] = "CLEAN" if ok2 else "FAIL"
        if ok2:
            report["c7_w3_apply"] = "APPLIED" if apply(f"/home/z/my-project/{OUT}/c7_w3_on_w2.patch", c7, "C7 w3 apply") else "FAIL"
# also: does w3 apply directly on main? (informational)
main_wt = wt_at("main", "c7main")
if main_wt:
    ok = check_apply(f"/home/z/my-project/{OUT}/c7_w1w2_on_s170.patch", main_wt, "C7 w1w2 on main (info)")
    report["c7_w1w2_on_main"] = "CLEAN" if ok else "FAIL"

# ── C9: 25b5a01 worktree; also try directly on main ──────────────────────
c9 = wt_at("25b5a01b2313d681d2dd24d1d4c108110f13395a", "c9")
if c9:
    ok1 = check_apply(f"/home/z/my-project/{OUT}/coder9_phase1.patch", c9, "C9 p1 on 25b5a01")
    report["c9_p1_on_25b5a01"] = "CLEAN" if ok1 else "FAIL"
    if ok1 and apply(f"/home/z/my-project/{OUT}/coder9_phase1.patch", c9, "C9 p1 apply"):
        ok2 = check_apply(f"/home/z/my-project/{OUT}/coder9_phase2_harness.patch", c9, "C9 p2 on p1-tree")
        report["c9_p2_on_p1tree"] = "CLEAN" if ok2 else "FAIL"
c9m = wt_at("main", "c9main")
if c9m:
    ok = check_apply(f"/home/z/my-project/{OUT}/coder9_phase1.patch", c9m, "C9 p1 on main (info)")
    report["c9_p1_on_main"] = "CLEAN" if ok else "FAIL"

# ── C8: ea490b82 + w1..5 tree patch → wave6 ──────────────────────────────
c8 = wt_at("ea490b828cfa7626531fcca27b2aff1876e9d2fa", "c8")
if c8:
    ok1 = check_apply(f"/home/z/my-project/{OUT}/c8_w1_5_tree.patch", c8, "C8 w1..5 on ea490b82")
    report["c8_w15_on_ea490b82"] = "CLEAN" if ok1 else "FAIL"
    if ok1 and apply(f"/home/z/my-project/{OUT}/c8_w1_5_tree.patch", c8, "C8 w1..5 apply"):
        ok2 = check_apply(f"/home/z/my-project/{OUT}/c8_wave6.patch", c8, "C8 w6 on w1..5-tree")
        report["c8_w6_applycheck"] = "CLEAN" if ok2 else "FAIL"
        if ok2:
            report["c8_w6_apply"] = "APPLIED" if apply(f"/home/z/my-project/{OUT}/c8_wave6.patch", c8, "C8 w6 apply") else "FAIL"
            # quantify divergence of the composed C8 tree vs main for the shared files
            for f in ["miniandroid/src/dex/dalvik_engine.cpp", "miniandroid/src/dex/dalvik_engine.h"]:
                rc, o, e = git("diff", "--stat", "main" if False else "HEAD", "--", f, cwd=c8)  # placeholder
            # compare against main blob
            for f in ["miniandroid/src/dex/dalvik_engine.cpp"]:
                r = subprocess.run(["git", "show", f"main:{f}"], capture_output=True, cwd=c8)
                main_bytes = r.stdout if r.returncode == 0 else b""
                p = os.path.join(c8, f)
                their = open(p, "rb").read() if os.path.exists(p) else b""
                report["c8_dalvik_vs_main_bytes"] = [len(their), len(main_bytes)]
                import difflib
                a = main_bytes.decode(errors="replace").splitlines()
                b = their.decode(errors="replace").splitlines()
                d = list(difflib.unified_diff(a, b, lineterm=""))
                plus = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
                minus = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
                report["c8_dalvik_vs_main_diff"] = f"+{plus}/-{minus} lines (main -> their w1..5+w6 tree)"
                print(f"[C8] dalvik_engine.cpp vs main: +{plus}/-{minus} lines ({len(their)} vs {len(main_bytes)} bytes)")

json.dump(report, open(f"{OUT}/s177_applycheck.json", "w"), indent=1)
print(json.dumps(report, indent=1))
