#!/usr/bin/env python3
"""S-HYGIENE artifact classifier + duplicate detector + policy guard.

Scans every TRACKED file, classifies it into the artifact lifecycle vocabulary,
detects duplicate content by SHA256, and checks repository policy
(zero APK/AAB, no build dirs, no raw logs, no secrets, size limits).

Output: docs/ARTIFACT_REGISTRY.json  (machine registry; deterministic)
Exit code: number of POLICY violations (0 = pass).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

REPO = "/home/z/my-project"
OUT = os.path.join(REPO, "docs/ARTIFACT_REGISTRY.json")

SECRET_PATTERNS = [
    re.compile(p) for p in (
        r"ghp_[A-Za-z0-9]{30,}", r"github_pat_[A-Za-z0-9_]{20,}",
        r"AKIA[0-9A-Z]{16}", r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
        r"xox[baprs]-[A-Za-z0-9-]{10,}", r"AIza[0-9A-Za-z_-]{35}",
    )
]


def git(*args):
    r = subprocess.run(["git", "-C", REPO] + list(args), capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode()[:300])
    return r.stdout


def classify(path: str, size: int) -> str:
    p = path.lower()
    # policy-obvious classes first
    if p.endswith((".apk", ".aab")):
        return "POLICY_VIOLATION_APK"
    if p.endswith((".o", ".obj")) or p.startswith(("miniandroid/build/", "build/")):
        return "BUILD_ARTIFACT"
    if p.endswith((".log",)) or "/logs/" in p:
        # curated/distilled logs referenced by canonical evidence are evidence
        if p.startswith(("docs/evidence/mc4_telegram/tg_run", "docs/evidence/s60_r380/")):
            return "CANONICAL_EVIDENCE"
        return "RAW_LOG"
    # canonical source trees
    if p.startswith(("miniandroid/src/", "miniandroid/third_party/", "games/",
                     "scripts/", "tools/", "examples/", "miniandroid/scripts/",
                     "miniandroid/tests/")) and p.endswith(
            (".cpp", ".cc", ".h", ".hpp", ".py", ".sh", ".java", ".md",
             ".txt", ".mk", ".am", ".cmake", ".json", ".xml", ".c")):
        return "CANONICAL_SOURCE"
    if os.path.basename(path) in ("Makefile", ".gitignore", "LICENSE",
                                  "CONSTITUTION_V2.md", "README.md") or p.endswith((".mk",)):
        return "CANONICAL_SOURCE"
    # fixtures
    if (p.startswith("fixtures/") or p.endswith((".dex", ".wav", ".bin"))
            or "/golden" in p or p.startswith(("miniandroid/tests/fixtures/",
                                                "miniandroid/tests/fixtures_foundation/",
                                                "docs/assets/"))):
        return "CANONICAL_FIXTURE"
    # pinned upstream reference sources (before generic docs/ rules)
    if p.startswith("upstream/") or p.startswith("docs/upstream/"):
        return "REFERENCE_SOURCE_PINNED"
    # canonical evidence / knowledge trees
    if p.startswith(("docs/evidence/", "docs/achievements/", "docs/history/",
                     "docs/research/", "docs/forensics/", "docs/corpus/",
                     "docs/foundation/", "docs/runtime/", "docs/audit/",
                     "docs/demos/", "docs/development/", "docs/decisions/",
                     "docs/execution-skill/", "docs/knowledge/",
                     "docs/agent-index/", "docs/architecture/",
                     "miniandroid/docs/", "miniandroid/database/",
                     "registry/", "evidence/")):
        return "CANONICAL_EVIDENCE"
    if p.startswith("docs/build/"):
        return "CANONICAL_DOC"
    if p.endswith((".gif", ".png", ".jpg", ".jpeg", ".ppm", ".webp")):
        return "VISUAL_EVIDENCE_UNSCOPED"
    if p.endswith((".md", ".json", ".jsonl", ".csv", ".xml", ".yaml", ".yml", ".txt")):
        return "CANONICAL_DOC"
    if p.endswith((".jar", ".zip", ".tar", ".gz", ".7z", ".so")):
        return "ARCHIVE_BINARY"
    return "UNKNOWN"


def main():
    files = git("ls-files").decode().splitlines()
    registry = defaultdict(lambda: {"count": 0, "bytes": 0, "paths": []})
    dup_groups = defaultdict(list)
    violations = []
    oversize = []
    total_bytes = 0
    for f in files:
        fp = os.path.join(REPO, f)
        try:
            with open(fp, "rb") as fh:
                data = fh.read()
        except OSError:
            continue
        size = len(data)
        total_bytes += size
        cls = classify(f, size)
        registry[cls]["count"] += 1
        registry[cls]["bytes"] += size
        if len(registry[cls]["paths"]) < 400:
            registry[cls]["paths"].append(f)
        dup_groups[hashlib.sha256(data).hexdigest()].append((f, size))
        if cls.startswith("POLICY_VIOLATION"):
            violations.append((f, cls))
        if cls in ("RAW_LOG", "BUILD_ARTIFACT"):
            violations.append((f, cls))
        if size > 1_000_000:
            oversize.append((size, f))
        low = data[:4096].decode("utf-8", "ignore")
        for pat in SECRET_PATTERNS:
            if pat.search(low) and not f.endswith((".md", ".txt")):
                violations.append((f, "SECRET_PATTERN"))
                break

    duplicates = []
    for sha, locs in dup_groups.items():
        if len(locs) > 1 and locs[0][1] > 0:
            duplicates.append({
                "sha256": sha, "size": locs[0][1], "copies": len(locs),
                "locations": sorted(l[0] for l in locs),
                "reclaimable_bytes": locs[0][1] * (len(locs) - 1),
            })
    duplicates.sort(key=lambda d: -d["reclaimable_bytes"])

    out = {
        "schema": "miniandroid.artifact_registry.v1",
        "generated_by": "tools/artifact_classifier.py",
        "tracked_files": len(files),
        "tracked_bytes": total_bytes,
        "classes": {k: {"count": v["count"], "bytes": v["bytes"],
                        "sample_paths": sorted(v["paths"])[:40]}
                    for k, v in sorted(registry.items())},
        "policy_violations": [{"path": f, "class": c} for f, c in violations],
        "oversize_files_gt_1mb": [{"bytes": s, "path": f} for s, f in sorted(oversize, reverse=True)],
        "duplicate_groups": duplicates[:100],
        "duplicate_groups_total": len(duplicates),
        "duplicate_reclaimable_bytes": sum(d["reclaimable_bytes"] for d in duplicates),
    }
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)

    print(f"tracked: {len(files)} files, {total_bytes/1048576:.1f}MB")
    for k, v in sorted(registry.items(), key=lambda kv: -kv[1]["bytes"]):
        print(f"  {k:28s} {v['count']:5d} files {v['bytes']/1048576:8.2f}MB")
    print(f"policy violations: {len(violations)}")
    for f, c in violations[:15]:
        print(f"  VIOLATION {c}: {f}")
    print(f"oversize >1MB: {len(oversize)}")
    print(f"duplicate groups: {len(duplicates)}, reclaimable: "
          f"{out['duplicate_reclaimable_bytes']/1024:.0f}KB")
    for d in duplicates[:12]:
        print(f"  DUP {d['size']:8d}B x{d['copies']} {d['locations'][0]}")
    return len(violations)


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
