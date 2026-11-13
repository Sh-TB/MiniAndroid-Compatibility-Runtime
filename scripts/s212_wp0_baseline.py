#!/usr/bin/env python3
"""S212/WP0 — freeze the release baseline for #587 (RELEASE-0.0.6.2).

Measures, separately and honestly:
  - exact HEAD / branch / tree / working-tree state
  - toolchain versions
  - tracked path counts, path-summed blob bytes, unique blob count, duplicate groups
  - tracked checkout bytes (materialized working tree, excl .git)
  - fresh-clone checkout bytes + fresh-clone .git bytes
  - GitHub metadata size (API) — never substituted for the other measurements

Outputs (compact, no raw API dumps):
  evidence/s212/wp0_baseline/baseline.json       machine record
  evidence/s212/wp0_baseline/baseline.md         human summary
"""
import json
import subprocess
import hashlib
import datetime
from pathlib import Path
from collections import defaultdict

BASE = Path("/home/z/my-project")
OUT = BASE / "evidence/s212/wp0_baseline"
OUT.mkdir(parents=True, exist_ok=True)


def run(cmd, cwd=BASE):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600).stdout.strip()
    except FileNotFoundError:
        return ""
    except subprocess.TimeoutExpired:
        return ""


head = run(["git", "rev-parse", "HEAD"])
tree = run(["git", "rev-parse", "HEAD^{tree}"])
branch = run(["git", "branch", "--show-current"])
dirty = run(["git", "status", "--porcelain"])
describe = run(["git", "describe", "--tags", "--abbrev=0"])
tool = {
    "git": run(["git", "--version"]),
    "gpp": run(["g++", "--version"]) .splitlines()[0] if run(["g++", "--version"]) else "",
    "cmake": run(["cmake", "--version"]).splitlines()[0] if run(["cmake", "--version"]) else "",
    "python": run(["python3", "--version"]),
    "os": run(["uname", "-srmo"]),
}

# --- tracked paths, sizes, duplicates (authoritative: git ls-files + ls-tree -r -l)
paths = run(["git", "ls-files"]).splitlines()
n_paths = len(paths)
ls_tree = run(["git", "ls-tree", "-r", "-l", "HEAD"]).splitlines()
blob_bytes = 0
blob_sha_count = defaultdict(int)      # sha -> count of paths
blob_sha_size = {}
for line in ls_tree:
    parts = line.split()
    if len(parts) >= 4 and parts[1] == "blob":
        size = int(parts[3].split("\t")[0])
        sha = parts[2]
        blob_bytes += size
        blob_sha_count[sha] += 1
        blob_sha_size[sha] = size
n_unique_blobs = len(blob_sha_count)
dup_groups = {sha: c for sha, c in blob_sha_count.items() if c > 1}
dup_wasted = sum(blob_sha_size[sha] * (c - 1) for sha, c in dup_groups.items())

# --- materialized checkout bytes (tracked files only, excludes .git)
tracked_bytes = 0
for p in paths:
    f = BASE / p
    try:
        if f.is_symlink():
            tracked_bytes += len(str(f.readlink()))
        elif f.is_file():
            tracked_bytes += f.stat().st_size
    except OSError:
        pass

# --- .git directory size (local object store, may include fetched refs)
git_dir_bytes = int(run(["bash", "-c", "du -sb .git | cut -f1"]))

# --- GitHub metadata (API, unauthenticated is fine for this field)
github_size_kb = None
try:
    tok = subprocess.run(["bash", "-c", 'printf "protocol=https\\nhost=github.com\\n" | git credential fill 2>/dev/null | grep "^password=" | cut -d= -f2'],
                         capture_output=True, text=True).stdout.strip()
    import urllib.request
    req = urllib.request.Request(
        "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime",
        headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
                 "User-Agent": "miniandroid-wp0"})
    meta = json.load(urllib.request.urlopen(req, timeout=60))
    github_size_kb = meta.get("size")
except Exception as e:
    github_size_kb = None

record = {
    "captured_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "issue": "Sh-TB/MiniAndroid-Compatibility-Runtime#587 (RELEASE-0.0.6.2)",
    "head": head,
    "tree": tree,
    "branch": branch,
    "last_tag": describe,
    "working_tree_clean": dirty == "",
    "dirty_entries": dirty.splitlines(),
    "toolchain": tool,
    "paths": {
        "tracked_file_paths": n_paths,
        "path_summed_blob_bytes": blob_bytes,
        "path_summed_blob_mib": round(blob_bytes / (1024 * 1024), 2),
        "unique_blobs": n_unique_blobs,
        "duplicate_groups": len(dup_groups),
        "duplicate_wasted_checkout_bytes": dup_wasted,
        "duplicate_wasted_mib": round(dup_wasted / (1024 * 1024), 2),
    },
    "measurements": {
        "tracked_checkout_bytes": tracked_bytes,
        "tracked_checkout_mib": round(tracked_bytes / (1024 * 1024), 2),
        "local_git_dir_bytes": git_dir_bytes,
        "local_git_dir_mib": round(git_dir_bytes / (1024 * 1024), 2),
        "github_metadata_size_kb": github_size_kb,
        "github_metadata_mib": round(github_size_kb / 1024, 2) if github_size_kb else None,
        "note": "GitHub metadata size is GitHub's own pack estimate and is NOT any of the local measurements; checkout bytes count tracked paths materialized; path-summed blob bytes count ls-tree sizes with duplicates per path.",
    },
}
(OUT / "baseline.json").write_text(json.dumps(record, indent=1))

# --- duplicate group top list (compact: top 25)
top_dups = sorted(dup_groups.items(), key=lambda kv: -kv[1] * blob_sha_size[kv[0]])[:25]
md = []
md.append(f"# WP0 baseline — frozen for #587 (RELEASE-0.0.6.2)\n")
md.append(f"* Captured: {record['captured_utc']}")
md.append(f"* HEAD `{head}` · tree `{tree}` · branch `{branch}` · last tag `{describe}` · working tree clean: {record['working_tree_clean']}")
md.append(f"* Toolchain: {tool['gpp']} · {tool['cmake']} · {tool['python']} · {tool['os']}")
md.append("")
md.append("| Metric | Value |")
md.append("|---|---:|")
md.append(f"| Tracked file paths | {n_paths} |")
md.append(f"| Path-summed blob bytes | {blob_bytes} ({record['paths']['path_summed_blob_mib']} MiB) |")
md.append(f"| Unique blobs | {n_unique_blobs} |")
md.append(f"| Duplicate SHA groups | {len(dup_groups)} |")
md.append(f"| Duplicate checkout waste | {record['paths']['duplicate_wasted_mib']} MiB |")
md.append(f"| Tracked checkout bytes (materialized, excl .git) | {tracked_bytes} ({record['measurements']['tracked_checkout_mib']} MiB) |")
md.append(f"| Local .git dir bytes | {git_dir_bytes} ({record['measurements']['local_git_dir_mib']} MiB) |")
md.append(f"| GitHub metadata size | {github_size_kb} KB ({record['measurements']['github_metadata_mib']} MiB) |")
md.append("")
md.append("Top duplicate groups (blob sha16 · paths · size each · checkout waste):")
for sha, c in top_dups:
    md.append(f"* `{sha[:16]}` × {c} paths × {blob_sha_size[sha]} B each → waste {blob_sha_size[sha]*(c-1)} B")
(OUT / "baseline.md").write_text("\n".join(md) + "\n")

print(json.dumps({k: record[k] for k in ("head", "tree", "branch", "last_tag", "working_tree_clean")}, indent=1))
print("paths:", record["paths"])
print("measurements:", record["measurements"])
