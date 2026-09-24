#!/usr/bin/env python3
"""S94 Phase F: emit docs/GRAPHICS_SOURCE_REGISTRY.json (+ compute stats).

Merges Phase A/B verification + Phase C deep-mining evidence into the permanent
registry. Deep-inspection status is computed from actual fetched artifacts:
  DEEP_CLONE    - repo shallow-cloned and key files harvested
  DEEP_FETCH    - provenance-pinned source files fetched with symbol hits
  IDENTITY_ONLY - ls-remote verified; README/license-level evidence only
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/home/z/my-project")
BASE = ROOT / "run/s94/source_mining"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

repos = json.loads((BASE / "repositories.json").read_text())
clones = {c["repository"]: c for c in json.loads((BASE / "clones_harvest.json").read_text())["clones"]}
raw = {r["repository"]: r for r in json.loads((BASE / "rawfetch_results.json").read_text())["results"]}
s2l = json.loads((BASE / "source_to_law.json").read_text())
gap = json.loads((BASE / "gap_map.json").read_text())
sample = json.loads((BASE / "random_sample.json").read_text())

# law ids per repo
laws_by_repo = {}
for l in s2l["laws"]:
    laws_by_repo.setdefault(l["source"]["repository"], []).append(l["law_id"])


def inspect_status(repo):
    c = clones.get(repo)
    if c and c.get("files"):
        return "DEEP_CLONE", len(c["files"]), sum(f.get("bytes", 0) for f in c["files"])
    r = raw.get(repo, {})
    ok_files = [f for f in r.get("files", []) if f.get("status") == "OK"]
    if ok_files:
        return "DEEP_FETCH", len(ok_files), sum(f.get("bytes", 0) for f in ok_files)
    if (c and c.get("clone_head_sha")) or r.get("readme"):
        return "IDENTITY_ONLY", 0, 0
    return "IDENTITY_ONLY", 0, 0


entries = []
for rec in repos["repositories"]:
    repo = rec["repository"]
    status, nfiles, nbytes = inspect_status(repo)
    e = {
        "id": rec["id"],
        "repository": repo,
        "url": rec["url"],
        "status": rec["status"],
        "default_branch": rec.get("default_branch"),
        "head_sha": rec.get("head_sha"),
        "families": rec["families"],
        "priority": rec["priority"],
        "relationship": rec["relationship"],
        "seed_entry": rec["seed_entry"],
        "identity_history": rec.get("identity_history"),
        "upstream_url": rec.get("upstream_url"),
        "license": rec.get("license"),
        "license_class": rec.get("license_class"),
        "reuse_class": rec.get("reuse_class"),
        "license_evidence": rec.get("license_evidence"),
        "inspection_status": status,
        "inspected_files": nfiles,
        "inspected_bytes": nbytes,
        "law_ids": laws_by_repo.get(repo, []),
        "last_verified": rec.get("last_verified"),
        "directive_note": rec.get("directive_note"),
    }
    entries.append(e)

verified = [e for e in entries if e["status"] == "VERIFIED"]
deep = [e for e in verified if e["inspection_status"] in ("DEEP_CLONE", "DEEP_FETCH")]

doc = {
    "campaign": "S94 GRAPHICS SOURCE LIBRARY",
    "law": "GRAPHICS SOURCE-FIRST LAW (CONSTITUTION V2 section 170)",
    "generated_at": NOW,
    "verification": {
        "identity_method": "git ls-remote --symref (no GitHub API)",
        "license_method": "raw.githubusercontent.com at pinned HEAD SHA",
        "deep_mining_methods": ["shallow clone + file harvest", "pinned-SHA raw fetch with symbol line hits", "googlesource ?format=TEXT (minikin, View.java)"],
    },
    "counts": {
        "registry_entries": len(entries),
        "distinct_github_verified_repositories": len(verified),
        "off_github_canonical_references": sum(1 for e in entries if e["status"] == "OFF_GITHUB"),
        "unverified_directive_identities": sum(1 for e in entries if e["status"] not in ("VERIFIED", "OFF_GITHUB")),
        "deep_inspected": len(deep),
        "identity_only": sum(1 for e in verified if e["inspection_status"] == "IDENTITY_ONLY"),
    },
    "entries": entries,
}
(ROOT / "docs/GRAPHICS_SOURCE_REGISTRY.json").write_text(json.dumps(doc, indent=1))
print(json.dumps(doc["counts"], indent=1))
print("laws:", len(s2l["laws"]), "| findings:", sum(1 for _ in open(BASE / "findings.jsonl")),
      "| impls:", sum(1 for _ in open(BASE / "implementations.jsonl")),
      "| tests:", sum(1 for _ in open(BASE / "tests.jsonl")))
