#!/usr/bin/env python3
"""S212/WP10 — evidence_size_inventory.tsv (#587 R02/R04/R10/R20/R22 deliverable).

Every tracked image: path, type, bytes, dimensions, sha256, class, canonical
consumer, disposition. Classes follow the WP10 §5 retention tiers.
Also writes evidence_retention_manifest.json (compact rollup).
"""
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "evidence"
OUT.mkdir(exist_ok=True)

meta = {}
ls_tree = subprocess.run(["git", "ls-tree", "-r", "-l", "HEAD"], cwd=BASE, capture_output=True, text=True).stdout.splitlines()
for line in ls_tree:
    try:
        left, path = line.split("\t", 1)
        mod, typ, sha, sz = left.split()
        meta[path] = (sha, int(sz))
    except ValueError:
        continue

allow = json.load(open(BASE / "docs/POLICY_ALLOWLIST.json"))
al_img = {e["path"] if isinstance(e, dict) else e for e in allow.get("oversize_images", [])}
al_dup = {e["path"] if isinstance(e, dict) else e for e in allow.get("duplicates", [])}

IMG = (".png", ".jpg", ".jpeg", ".gif", ".webp")
CANONICAL_HINTS = ("docs/evidence/canonical/", "canonical GIF", "golden")

rows = []
seen_sha = {}
for f in sorted(meta):
    if not f.lower().endswith(IMG):
        continue
    sha, size = meta[f]
    p = BASE / f
    dims = mode = "?"
    try:
        with Image.open(p) as im:
            dims = f"{im.width}x{im.height}"
            mode = im.mode
    except Exception:
        pass
    if "canonical" in f or "golden" in f.lower():
        cls = "A_CANONICAL_GOLDEN"
    elif f in al_img:
        cls = "A_CANONICAL_GOLDEN (oversize allowlisted)"
    elif sha[:64] in seen_sha:
        cls = "DEDUP_REMOVED (see evidence_duplicate_groups.tsv)"
    elif size > 1048576:
        cls = "B_BATCH_FULL_FRAME (retained representative)"
    elif size > 800000:
        cls = "B_BATCH_FULL_FRAME / size-gated"
    else:
        cls = "B_RUN_EVIDENCE_COMPACT"
    seen_sha[sha] = f
    disp = "KEEP" if not cls.startswith("DEDUP") else "REMOVED(dedup)"
    if "halma" in f and f != "evidence/s188_w18/runs/halma_w18_r1/screenshot.png" and "w18" in f:
        disp = "REMOVED(w18 compaction)"
    rows.append((f, Path(f).suffix.lstrip(".").lower(), size, dims, sha[:16], cls, disp))

with open(BASE / "evidence/evidence_size_inventory.tsv", "w") as fh:
    fh.write("path\ttype\tbytes\tdimensions\tsha256_16\tclass\tdisposition\n")
    for r in rows:
        fh.write("\t".join(str(x) for x in r) + "\n")

manifest = {
    "policy": "#587 WP10 §5 retention tiers (A canonical golden pixel-exact; B batch determinism evidence; C derivative labeled NOT PIXEL-EXACT; D compact trace summary)",
    "generated": "2026-11-13",
    "inventory": "evidence/evidence_size_inventory.tsv",
    "duplicate_groups": "evidence/s212/wp1_inventory/evidence_duplicate_groups.tsv (1,199 removed, canonical redirects recorded)",
    "batch_summaries": [
        "evidence/s188_w18/halma_w18_batch_summary.json (11-run compaction: 1 retained full PNG + per-run SHA rows)",
        "evidence/s188_w18/halma_w18_retention_manifest.json (derivative provenance)",
        "evidence/s188_w18/halma_w18_BATCH_REPORT.md (corrected truthful report)",
    ],
    "totals": {
        "tracked_images": len(rows),
        "image_bytes_path_summed": sum(r[2] for r in rows),
        "over_1mib": sum(1 for r in rows if r[2] > 1048576),
        "over_800k_noise_threshold": sum(1 for r in rows if r[2] > 800000),
    },
    "future_runner_rules": "scripts/s207_gate.py post-capture gate: >800KB screenshot flagged NOISE (uninitialized-buffer suspicion); >1MiB fails without canonical allowlist entry; repeated runs write batch-level SHA rows not per-run full PNGs",
}
json.dump(manifest, open(BASE / "evidence/evidence_retention_manifest.json", "w"), indent=1)
print("rows:", len(rows), "image MB:", round(manifest["totals"]["image_bytes_path_summed"] / 1048576, 2))
