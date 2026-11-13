#!/usr/bin/env python3
"""S212/WP1 — full tracked-tree inventory + classification for #587 R02.

Classifies every tracked path by area and artifact class using path+content
rules. Produces:
  evidence/s212/wp1_inventory/inventory.tsv.gz     full 16k-row inventory (gz, compact)
  evidence/s212/wp1_inventory/inventory_summary.md area x class counts
  evidence/s212/wp1_inventory/noise_candidates.tsv candidates with rule-based disposition
"""
import gzip
import hashlib
import subprocess
import re
from pathlib import Path
from collections import defaultdict, Counter

BASE = Path("/home/z/my-project")
OUT = BASE / "evidence/s212/wp1_inventory"
OUT.mkdir(parents=True, exist_ok=True)

paths = subprocess.run(["git", "ls-files"], cwd=BASE, capture_output=True,
                       text=True).stdout.splitlines()

# blob sizes from ls-tree
sizes = {}
ls_tree = subprocess.run(["git", "ls-tree", "-r", "-l", "HEAD"], cwd=BASE,
                         capture_output=True, text=True).stdout.splitlines()
for line in ls_tree:
    parts = line.split()
    if len(parts) >= 4 and parts[1] == "blob":
        sizes[parts[4] if len(parts) > 4 else line.split("\t")[1]] = None

# simpler: build map path->(mode, type, sha, size)
meta = {}
for line in ls_tree:
    try:
        left, path = line.split("\t", 1)
        mode, typ, sha, sz = left.split()
        meta[path] = (sha, int(sz))
    except ValueError:
        continue

IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
DB_EXT = {".sqlite3", ".sqlite", ".db", ".wal", ".shm"}
CACHE_EXT = {".pyc", ".pyo", ".o", ".so", ".a"}
LOG_PAT = re.compile(r"(console\.log$|_out\d*\.txt$|_err\d*\.txt$|gate_out|\.log$|stderr|stdout)", re.I)
STORE_PAT = re.compile(r"(^|/)store_[^/]+/(data|cache|code_cache)/", re.I)


def classify(path: str, size: int, sha: str) -> str:
    p = path.lower()
    ext = Path(path).suffix.lower()
    # stores / run residue
    if STORE_PAT.search(path):
        return "RUN_STORE_RESIDUE"
    if DB_EXT.__contains__(ext) or p.endswith("-wal") or p.endswith("-shm") or p.endswith("-lock"):
        return "DB_WAL_SHM_LOCK"
    if ext in CACHE_EXT:
        return "BINARY_CACHE_OBJ"
    if LOG_PAT.search(path):
        return "RAW_LOG_OUTPUT"
    if ext == ".apk":
        return "APK_BINARY"
    if ext == ".deb":
        return "DEB_PACKAGE"
    if ext in IMG_EXT:
        return "IMAGE_EVIDENCE"
    if ext == ".json" or ext == ".jsonl":
        # big raw API dumps
        if re.search(r"(issues_all|all_issue_comments|comments_raw|commits\.json|s220_issues|issue_.*_comments)", p):
            return "RAW_API_DUMP"
        return "JSON_REGISTRY_OR_DATA"
    if ext in {".gz", ".tgz", ".tar", ".zip"}:
        return "ARCHIVE"
    # areas
    if path.startswith("miniandroid/src/") or path.startswith("miniandroid/include/") or path == "miniandroid/Makefile" or path == "miniandroid/CMakeLists.txt":
        return "RUNTIME_SOURCE"
    if path.startswith(("tests/", "miniandroid/tests/")):
        return "TEST"
    if path.startswith("fixtures/"):
        return "FIXTURE"
    if path.startswith(("docs/",)):
        return "DOCS"
    if path.startswith("scripts/") or path.startswith("tools/"):
        return "SCRIPT_TOOL"
    if path.startswith("canonical/") or path.startswith("registry/") or path == "root_registry.json":
        return "REGISTRY"
    if path.startswith("evidence/"):
        return "EVIDENCE_OTHER"
    if path.startswith("third_party/"):
        return "THIRD_PARTY_VENDORED"
    if path.startswith(("upstream/", "reference/", "docs/upstream/")):
        return "UPSTREAM_REFERENCE_SOURCE"
    if path.startswith("forensic_data/"):
        return "FORENSIC_RAW"
    if path.startswith("games/"):
        return "GAME_SOURCE"
    if path.startswith("library_ecosystem/"):
        return "LIBRARY_METADATA"
    if ext in {".cpp", ".cc", ".h", ".hpp", ".java", ".kt", ".c"}:
        return "SOURCE_OTHER"
    if ext in {".md", ".txt", ".rst"}:
        return "DOC_TEXT"
    if ext in {".sh", ".py"}:
        return "SCRIPT_OTHER"
    return "OTHER"


rows = []
for p in paths:
    sha, size = meta.get(p, ("", 0))
    cls = classify(p, size, sha)
    rows.append((p, size, sha[:16], cls))

# summary
area_cls = defaultdict(Counter)
cls_bytes = Counter()
area_bytes = Counter()
for p, size, sha16, cls in rows:
    area = p.split("/")[0] if "/" in p else "(root)"
    area_cls[area][cls] += 1
    cls_bytes[cls] += size
    area_bytes[area] += size

# full inventory (gz)
with gzip.open(OUT / "inventory.tsv.gz", "wt", newline="") as f:
    f.write("path\tbytes\tblob_sha16\tclass\n")
    for p, size, sha16, cls in rows:
        f.write(f"{p}\t{size}\t{sha16}\t{cls}\n")

# summary md
md = ["# WP1 inventory summary (R02)", "",
      f"Total tracked paths: {len(rows)}", "",
      "## Bytes by class", "", "| class | paths | bytes |", "|---|---:|---:|"]
cls_n = Counter(r[3] for r in rows)
for cls, b in cls_bytes.most_common():
    md.append(f"| {cls} | {cls_n[cls]} | {b} |")
md += ["", "## Bytes by top-level area", "", "| area | paths | bytes |", "|---|---:|---:|"]
for area, b in sorted(area_bytes.items(), key=lambda kv: -kv[1])[:30]:
    md.append(f"| {area} | {sum(area_cls[area].values())} | {b} |")
md += ["", "## Area x class (top areas)", ""]
for area, b in sorted(area_bytes.items(), key=lambda kv: -kv[1])[:20]:
    md.append(f"### {area} ({sum(area_cls[area].values())} paths, {b} bytes)")
    for cls, n in area_cls[area].most_common():
        md.append(f"- {cls}: {n}")
    md.append("")
(OUT / "inventory_summary.md").write_text("\n".join(md) + "\n")

# noise candidates
CAND_CLASSES = {"RUN_STORE_RESIDUE", "DB_WAL_SHM_LOCK", "BINARY_CACHE_OBJ", "RAW_LOG_OUTPUT",
                "APK_BINARY", "DEB_PACKAGE", "RAW_API_DUMP", "ARCHIVE"}
with open(OUT / "noise_candidates.tsv", "w") as f:
    f.write("path\tbytes\tblob_sha16\tclass\trule\n")
    for p, size, sha16, cls in rows:
        if cls in CAND_CLASSES:
            f.write(f"{p}\t{size}\t{sha16}\t{cls}\n")

print(f"rows={len(rows)}")
print("class counts:", dict(cls_n.most_common()))
print("candidate paths:", sum(cls_n[c] for c in CAND_CLASSES))
print("summary + gz + candidates written to", OUT)
