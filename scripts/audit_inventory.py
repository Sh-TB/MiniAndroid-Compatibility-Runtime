#!/usr/bin/env python3
"""AUDIT-A: complete tracked-file inventory for Sh-TB/MiniAndroid-Compatibility-Runtime.
Outputs (download/repository_audit/):
  FULL_FILE_INVENTORY.csv   path,size,sha256,blob,last_commit,last_date
  DIRECTORY_REPORT.csv      dir,files,bytes
  LARGE_FILES_TOP500.csv    rank,path,size,sha256,blob
  DUPLICATE_GROUPS.csv      sha256,size,copies,paths(;)
Untracked/ignored local artifacts are NOT repo content and are reported separately.
"""
import csv, hashlib, os, subprocess, sys
from collections import defaultdict

ROOT = "/home/z/my-project"
OUT = os.path.join(ROOT, "download", "repository_audit")
os.makedirs(OUT, exist_ok=True)
os.chdir(ROOT)

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout

# 1. tracked files: path -> (blob, size)
print("ls-tree...", flush=True)
tree = {}
for line in run(["git", "ls-tree", "-r", "-l", "HEAD"]).splitlines():
    meta, path = line.split("\t", 1)
    mode, typ, blob, size = meta.split()
    tree[path] = (blob, int(size))
print(f"tracked: {len(tree)}", flush=True)

# 2. last-modifying commit per path (single pass)
print("log walk...", flush=True)
last = {}
log = run(["git", "log", "--name-only", "--format=@%H %cI"])
cur = None
for line in log.splitlines():
    if line.startswith("@"):
        parts = line[1:].split(" ", 1)
        cur = (parts[0][:12], parts[1][:10] if len(parts) > 1 else "")
    elif line and cur:
        if line not in last:
            last[line] = cur
print(f"commit map: {len(last)}", flush=True)

# 3. sha256 of each working-tree file (tracked)
print("sha256 pass...", flush=True)
sha = {}
missing = []
for i, path in enumerate(tree):
    p = os.path.join(ROOT, path)
    if not os.path.isfile(p):
        missing.append(path)
        sha[path] = ""
        continue
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    sha[path] = h.hexdigest()
    if i % 4000 == 0:
        print(f"  {i}/{len(tree)}", flush=True)
print(f"missing from worktree: {len(missing)}", flush=True)

# 4. FULL_FILE_INVENTORY.csv
with open(os.path.join(OUT, "FULL_FILE_INVENTORY.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["path", "size_bytes", "sha256", "git_blob", "last_commit", "last_date"])
    for path in sorted(tree):
        blob, size = tree[path]
        c, d = last.get(path, ("", ""))
        w.writerow([path, size, sha[path], blob, c, d])

# 5. DIRECTORY_REPORT.csv
dirs = defaultdict(lambda: [0, 0])
for path, (blob, size) in tree.items():
    d = os.path.dirname(path) or "."
    dirs[d][0] += 1
    dirs[d][1] += size
with open(os.path.join(OUT, "DIRECTORY_REPORT.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["dir", "files", "bytes"])
    for d, (n, b) in sorted(dirs.items(), key=lambda kv: -kv[1][1]):
        w.writerow([d, n, b])

# 6. LARGE_FILES_TOP500.csv
top = sorted(tree.items(), key=lambda kv: -kv[1][1])[:500]
with open(os.path.join(OUT, "LARGE_FILES_TOP500.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["rank", "path", "size_bytes", "sha256", "git_blob"])
    for r, (path, (blob, size)) in enumerate(top, 1):
        w.writerow([r, path, size, sha[path], blob])

# 7. DUPLICATE_GROUPS.csv (byte-identical, tracked)
groups = defaultdict(list)
for path, h in sha.items():
    if h:
        groups[h].append(path)
dups = {h: ps for h, ps in groups.items() if len(ps) > 1}
with open(os.path.join(OUT, "DUPLICATE_GROUPS.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["sha256", "size_bytes", "copies", "wasted_bytes", "paths(; )"])
    for h, ps in sorted(dups.items(), key=lambda kv: -tree[kv[1][0]][1]):
        ps = sorted(ps)
        size = tree[ps[0]][1]
        w.writerow([h, size, len(ps), size * (len(ps) - 1), "; ".join(ps)])
total_wasted = sum(tree[ps[0]][1] * (len(ps) - 1) for ps in dups.values())
tracked_bytes = sum(s for _, s in tree.values())
print(f"tracked_bytes={tracked_bytes} dup_groups={len(dups)} wasted={total_wasted}", flush=True)
print(json_summary := "DONE", flush=True)
