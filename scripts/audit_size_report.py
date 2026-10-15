#!/usr/bin/env python3
"""MA-RECON baseline/final repository size report (reproducible, stdlib only).

Measures (independently):
  - recursive git tree entry count (git ls-tree -r HEAD)
  - tracked file count (git ls-files)
  - sum of tracked per-path blob bytes (git ls-tree -r -l HEAD)
  - per-extension counts and byte totals (tracked)
  - largest tracked files
  - largest top-level directories (tracked bytes)
  - duplicate-content groups by blob SHA (extra path occurrences + bytes)
  - working-tree du (excluding .git) via os.walk
  - .git size via du + git count-objects -vH

Usage: python3 scripts/audit_size_report.py <out.json>
"""
import json
import os
import subprocess
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else "run/audit/size_report.json"


def git(*args):
    r = subprocess.run(["git", "-C", REPO] + list(args), capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode()[:400])
    return r.stdout


def du_bytes(root, exclude_git=True):
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        if exclude_git and ".git" in dirnames:
            dirnames.remove(".git")
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            try:
                if not os.path.islink(fp):
                    total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def main():
    head = git("rev-parse", "HEAD").decode().strip()
    # 1. recursive tree entries
    tree_lines = git("ls-tree", "-r", "-l", "HEAD").decode().splitlines()
    # format: <mode> <type> <sha> <size>\t<path>
    per_path = []  # (path, sha, size or None)
    for line in tree_lines:
        meta, path = line.split("\t", 1)
        parts = meta.split()
        sha, size = parts[2], parts[3]
        per_path.append((path, sha, None if size == "-" else int(size)))

    tracked_files = git("ls-files").decode().splitlines()
    tracked_set = set(tracked_files)

    # 2. per-extension totals
    ext_count = defaultdict(int)
    ext_bytes = defaultdict(int)
    for path, sha, size in per_path:
        base = os.path.basename(path)
        ext = base.lower().rsplit(".", 1)[-1] if "." in base else "(none)"
        ext_count[ext] += 1
        if size:
            ext_bytes[ext] += size

    # 3. largest tracked files
    largest = sorted(((s, p) for p, _, s in per_path if s), reverse=True)[:30]

    # 4. largest top-level dirs (tracked bytes)
    top_bytes = defaultdict(int)
    top_count = defaultdict(int)
    root_files_bytes = 0
    for path, _, size in per_path:
        size = size or 0
        top = path.split("/", 1)[0]
        if "/" in path:
            top_bytes[top] += size
            top_count[top] += 1
        else:
            top_bytes["(root files)"] += size
            top_count["(root files)"] += 1

    # 5. duplicate content groups
    groups = defaultdict(list)
    for path, sha, size in per_path:
        groups[sha].append((path, size or 0))
    dup_groups = {}
    dup_extra_paths = 0
    dup_extra_bytes = 0
    for sha, entries in groups.items():
        if len(entries) > 1:
            dup_groups[sha] = entries
            dup_extra_paths += len(entries) - 1
            dup_extra_bytes += sum(s for _, s in entries[1:])

    # 6. working tree + .git
    wt = du_bytes(REPO, exclude_git=True)
    gitdir = os.path.join(REPO, ".git")
    gsize = du_bytes(gitdir, exclude_git=False)
    co = subprocess.run(["git", "-C", REPO, "count-objects", "-vH"],
                        capture_output=True).stdout.decode()

    # tracked-only working tree bytes (files that exist on disk)
    tracked_wt = 0
    tracked_missing = 0
    for f in tracked_files:
        fp = os.path.join(REPO, f)
        if os.path.isfile(fp) and not os.path.islink(fp):
            tracked_wt += os.path.getsize(fp)
        else:
            tracked_missing += 1

    rep = {
        "head": head,
        "recursive_tree_entries": len(per_path),
        "tracked_files": len(tracked_files),
        "tracked_working_tree_bytes": tracked_wt,
        "tracked_missing_from_disk": tracked_missing,
        "sum_tree_blob_bytes": sum(s for _, _, s in per_path if s),
        "working_tree_du_bytes_excl_git": wt,
        "git_dir_du_bytes": gsize,
        "count_objects": co.strip(),
        "extension_totals": {
            e: {"count": ext_count[e], "bytes": ext_bytes[e]}
            for e in sorted(ext_bytes, key=lambda x: -ext_bytes[x])[:30]
        },
        "largest_files": [{"path": p, "bytes": s} for s, p in largest],
        "top_level_dirs": {
            k: {"paths": top_count[k], "bytes": top_bytes[k]}
            for k in sorted(top_bytes, key=lambda x: -top_bytes[x])
        },
        "dup_groups": len(dup_groups),
        "dup_extra_paths": dup_extra_paths,
        "dup_extra_bytes": dup_extra_bytes,
        "dup_top_groups": sorted(
            ({"sha16": sha[:16], "paths": [p for p, _ in es][:8],
              "n": len(es), "bytes": es[0][1]}
             for es in dup_groups.values()),
            key=lambda g: -(g["n"] - 1) * g["bytes"])[:20],
    }
    os.makedirs(os.path.dirname(os.path.join(REPO, OUT)), exist_ok=True)
    with open(os.path.join(REPO, OUT), "w") as fh:
        json.dump(rep, fh, indent=1)
    # console summary
    print(f"HEAD: {head}")
    print(f"recursive tree entries : {len(per_path)}")
    print(f"tracked files          : {len(tracked_files)}")
    print(f"sum tree blob bytes    : {rep['sum_tree_blob_bytes']:,} ({rep['sum_tree_blob_bytes']/1048576:.2f} MiB)")
    print(f"tracked wt bytes       : {tracked_wt:,} ({tracked_wt/1048576:.2f} MiB)")
    print(f"working tree du (excl .git): {wt:,} ({wt/1048576:.2f} MiB)")
    print(f".git du bytes          : {gsize:,} ({gsize/1048576:.2f} MiB)")
    print(f"dup groups             : {len(dup_groups)} groups, +{dup_extra_paths} paths, {dup_extra_bytes/1048576:.2f} MiB repeated path bytes")
    print("top-level dirs (MiB):")
    for k, v in list(rep["top_level_dirs"].items())[:15]:
        print(f"  {k:28s} {v['paths']:6d} paths  {v['bytes']/1048576:9.2f} MiB")
    print("top extensions:")
    for e, v in list(rep["extension_totals"].items())[:15]:
        print(f"  .{e:10s} {v['count']:6d}  {v['bytes']/1048576:9.2f} MiB")


if __name__ == "__main__":
    main()
