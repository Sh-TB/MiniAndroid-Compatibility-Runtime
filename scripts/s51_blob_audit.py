#!/usr/bin/env python3
"""S51 PHASE 1 — per-ref blob audit (bounded output, no file writes)."""
import subprocess, sys

REPO = "/home/z/my-project"

def run(args):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True)

def audit(ref):
    p = run(["git", "rev-list", "--objects", ref])
    if p.returncode != 0:
        print(f"{ref}: UNAVAILABLE ({p.stderr.strip()[:60]})")
        return
    sha_path = {}
    for line in p.stdout.splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2:
            sha_path[parts[0]] = parts[1]
    shas = list(sha_path.keys())
    total_blobs = 0
    total_bytes = 0
    big = []
    BATCH = 20000
    for i in range(0, len(shas), BATCH):
        inp = "\n".join(shas[i:i+BATCH])
        q = subprocess.run(
            ["git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
            cwd=REPO, input=inp, capture_output=True, text=True)
        for line in q.stdout.splitlines():
            parts = line.split()
            if len(parts) == 3 and parts[1] == "blob":
                size = int(parts[2])
                total_blobs += 1
                total_bytes += size
                if size > 1_000_000:
                    big.append((size, sha_path.get(parts[0], "?")))
    big.sort(reverse=True)
    ncommits = run(["git", "rev-list", "--count", ref]).stdout.strip()
    mb = total_bytes / 1048576
    bigmb = sum(b[0] for b in big) / 1048576
    print(f"== {ref} ==")
    print(f"   commits={ncommits} blobs={total_blobs} total={mb:.1f}MiB | blobs>1MB: {len(big)} = {bigmb:.1f}MiB")
    for size, path in big[:8]:
        print(f"   {size/1048576:8.2f}MiB  {path[:100]}")

for r in sys.argv[1:]:
    audit(r)
