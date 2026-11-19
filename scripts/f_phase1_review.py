#!/usr/bin/env python3
"""FINAL Phase 1: full PR #625 diff review at exact head 1e5c8fb9."""
import json, subprocess, re, os

cwd = "/home/z/my-project"
files = json.load(open("/tmp/f_phase0.json"))["pr625_files"]
print("=== PR625 all %d files (additions):" % len(files))
cats = {}
for x in sorted(files, key=lambda y: -y["a"]):
    ext = os.path.splitext(x["f"])[1] or x["f"].split("/")[-1]
    cats[ext] = cats.get(ext, [0, 0])
    cats[ext][0] += 1; cats[ext][1] += x["a"]
    print(f"  {x['a']:>7}  {x['f']}")
print("=== by extension:", json.dumps({k: v for k, v in sorted(cats.items())}, indent=1))

# binary / artifact scan in the actual diff
d = subprocess.run(["git", "diff", "--numstat", "125f5690", "1e5c8fb9"], capture_output=True, text=True, cwd=cwd).stdout
bins = [l for l in d.splitlines() if l.startswith("-\t")]
print("=== binary entries in diff:", bins or "NONE")
bad = [x["f"] for x in files if re.search(r"\.(apk|so|a|o|png|jpg|dex|zip|jar|rej|log|tmp|pyc)$|(^|/)(build|build_dev_so|corpus|handoff_apks|node_modules)/", x["f"])]
print("=== artifact-pattern files:", bad or "NONE")

# content checks at exact head, in a worktree
subprocess.run(["git", "worktree", "add", "--detach", "/tmp/wt625", "1e5c8fb9"], capture_output=True, cwd=cwd)
os.system("cd /tmp/wt625/miniandroid && make --no-print-directory -n all > /tmp/wt625_mn_all.txt 2>&1")
mn = open("/tmp/wt625_mn_all.txt").read()
print("=== 'make -n all' at 1e5c8fb9 references build_dev_so:", mn.count("build_dev_so"),
      "| total commands:", len(mn.splitlines()))
mk = open("/tmp/wt625/miniandroid/Makefile").read()
for pat, lab in [("dev-so-clean:", "rollback target"), ("DALVIK_SPLIT=0", "monolith fallback switch"),
                 ("libminiandroid_dalvik.so", "dev .so rule"), ("DALVIK_SPLIT ?= 1", "default static split")]:
    print(f"=== Makefile has {lab}: {pat in mk or pat.replace('?=','? =') in mk}")
os.system("cd /tmp/wt625/miniandroid && make --no-print-directory -n dev-so-test > /tmp/wt625_mn_dev.txt 2>&1; echo rc=$?")
dv = open("/tmp/wt625_mn_dev.txt").read()
print("=== 'make -n dev-so-test' plans commands:", len(dv.splitlines()), "| PIC rules present:", dv.count("-fPIC"))

# committed acceptance evidence at the exact head
ev = json.load(open("/tmp/wt625/miniandroid/evidence/wave9/w9_clean_results.json"))
print("=== w9_clean_results.json (committed in PR, at exact head):")
print(json.dumps(ev, indent=1)[:1500])
