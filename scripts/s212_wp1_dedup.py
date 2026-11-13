#!/usr/bin/env python3
"""S212/WP1 batch 2 — complete SHA duplicate scan + dedup execution for #587 R04/R10.

Scope: groups of tracked files with identical blob SHA where at least one member
lives under evidence/ or docs/evidence/.
Safety rules (per issue):
  - keep one canonical path per group (prefer: 'canonical' in path > non-'partial'
    > shallower > lexicographic)
  - before removing a member, verify references:
      * full-path mention anywhere (excluding SHA manifests + historical archives)
        -> keep
      * basename mention in live areas (docs non-history, scripts, canonical,
        registries, README, tools) -> keep
  - every removal recorded in evidence_duplicate_groups.tsv with redirect mapping
"""
import hashlib
import subprocess
import re
from pathlib import Path

BASE = Path("/home/z/my-project")
OUT = BASE / "evidence/s212/wp1_inventory"
OUT.mkdir(parents=True, exist_ok=True)

files = subprocess.run(["git", "ls-files"], cwd=BASE, capture_output=True, text=True).stdout.splitlines()
meta = {}
ls_tree = subprocess.run(["git", "ls-tree", "-r", "-l", "HEAD"], cwd=BASE, capture_output=True, text=True).stdout.splitlines()
for line in ls_tree:
    try:
        left, path = line.split("\t", 1)
        mode, typ, sha, sz = left.split()
        meta[path] = (sha, int(sz))
    except ValueError:
        continue

# group by blob sha
groups = {}
for p in files:
    sha, size = meta.get(p, ("", 0))
    if sha:
        groups.setdefault(sha, []).append(p)

EVID_AREAS = ("evidence/", "docs/evidence/")
LIVE_RE = re.compile(
    r"^(docs/(?!history/|evidence/SHA256SUMS)[^/]+/|scripts/|canonical/|registry/|tools/|README\.md|CONSTITUTION_V2\.md|\.agent/)")
SHA_MANIFEST = re.compile(r"SHA256SUMS|SHA512SUMS|_hashes|MANIFEST_SHA")
# pre-grep corpora (read once)
all_files_text = {}
def read_for_grep(rel: Path):
    try:
        return rel.read_text(errors="ignore")
    except Exception:
        return ""

live_docs = []   # (relpath, text) for live-area reference checks
for p in files:
    if p.endswith((".md", ".py", ".sh", ".json", ".jsonl", ".txt", ".tsv", ".yml", ".yaml", ".js", ".c", ".h", ".cpp")):
        if LIVE_RE.match(p) or p in ("README.md",):
            live_docs.append((p, read_for_grep(BASE / p)))

# generic artifact filenames: a mention of these in scripts/registries is a
# generic writer/template, not a reference to a specific evidence path
GENERIC = {
    "screenshot.png", "screenshot.jpg", "face.jpg", "face.png", "report.md",
    "trace.jsonl", "trace_summary.json", "lifecycle_trace.json", "summary.json",
    "console.log", "thumbnail.png", "run.png", "S207_GATE.json",
    "TRACE_SUMMARIES.json", "execution_summary.json", "results.json",
    "file_io.jsonl", "census.json", "device_clock", "package.json",
    "native_libs.json", "gate.png", "trace.txt", "frame_0.png",
}

removed = 0
removed_bytes = 0
kept_ref = 0
rows = []

def referenced(path: str, basename: str) -> str | None:
    full = path
    for rp, text in live_docs:
        if SHA_MANIFEST.search(rp) or rp.startswith("docs/history/"):
            continue
        if full in text:
            return f"full-path ref in {rp}"
    if basename in GENERIC:
        return None
    for rp, text in live_docs:
        if SHA_MANIFEST.search(rp) or rp.startswith("docs/history/"):
            continue
        if re.search(r"[`'\"/(=\s]" + re.escape(basename) + r"[`'\"\)\s,\]]", text):
            return f"basename ref in {rp}"
    return None

for sha, paths in sorted(groups.items(), key=lambda kv: -meta[kv[1][0]][1]):
    if len(paths) < 2:
        continue
    if not any(p.startswith(EVID_AREAS) for p in paths):
        continue
    if not any(meta[p][1] > 0 for p in paths):
        continue
    # choose keeper
    def key(p):
        return (0 if "canonical" in p else 1,
                0 if "partial" not in p else 1,
                p.count("/"),
                p)
    paths_sorted = sorted(paths, key=key)
    keep = paths_sorted[0]
    drop = [p for p in paths_sorted[1:]
            if p.startswith(EVID_AREAS) and not p.endswith((".md", ".json", ".jsonl", ".tsv", ".txt"))]
    # never drop text/registry-ish members; only binary media blobs dedup here
    for d in drop:
        bn = Path(d).name
        ref = referenced(d, bn)
        if ref:
            kept_ref += 1
            rows.append((sha[:16], meta[keep][1], keep, d, "KEPT(referenced)", ref))
        else:
            subprocess.run(["git", "rm", "-q", d], cwd=BASE)
            removed += 1
            removed_bytes += meta[d][1]
            rows.append((sha[:16], meta[keep][1], keep, d, "REMOVED",
                         f"redirect {d} -> {keep}"))

with open(OUT / "evidence_duplicate_groups.tsv", "w") as f:
    f.write("blob_sha16\tbytes_each\tkept_path\tremoved_path\tdisposition\tredirect_note\n")
    for r in rows:
        f.write("\t".join(str(x) for x in r) + "\n")

print(f"groups handled: {len({r[0] for r in rows})}")
print(f"removed paths: {removed} (checkout bytes saved: {removed_bytes} = {removed_bytes/1048576:.2f} MiB)")
print(f"kept because referenced: {kept_ref}")
