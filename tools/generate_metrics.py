#!/usr/bin/env python3
"""Single canonical source for public mutable counts (#587 R14/WP6).

Reads the canonical registries and emits docs/METRICS.json. README and release
docs MUST render counts from this file only; tools/check_readme_metrics.py
fails CI when a public summary drifts from here.

Regenerate: python3 tools/generate_metrics.py
"""
import json
import subprocess
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/METRICS.json"

can_reg = json.load(open(ROOT / "docs/evidence/canonical/registry.json"))["titles"]
games = json.load(open(ROOT / "canonical/game_registry.json"))["games"]
apps = json.load(open(ROOT / "canonical/app_registry.json"))["apps"]
roots = json.load(open(ROOT / "root_registry.json"))
roots = roots if isinstance(roots, list) else roots.get("roots", [])

status = Counter(t.get("status") for t in can_reg)
head = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
tree = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD^{tree}"], capture_output=True, text=True).stdout.strip()
n_files = int(subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True).stdout.count("\n"))

metrics = {
    "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "source_of_truth": {
        "titles": "docs/evidence/canonical/registry.json",
        "games": "canonical/game_registry.json",
        "apps": "canonical/app_registry.json",
        "roots": "root_registry.json (compatibility projection of canonical/root_cause_registry.json)",
        "head": "git",
    },
    "head": head,
    "tree": tree,
    "tracked_files": n_files,
    "canonical_titles_total": len(can_reg),
    "canonical_title_status": dict(status),
    "canonical_verified": status.get("VERIFIED", 0),
    "games_registered": len(games),
    "apps_registered": len(apps),
    "root_causes_total": len(roots),
    "abi_scope": "x86 / x86_64 only",
    "excluded_from_readme": [
        "S95/S125/S131-era campaign counters (stale)",
        "any count not present in this file",
    ],
}
OUT.write_text(json.dumps(metrics, indent=1) + "\n")
print(json.dumps({k: metrics[k] for k in ("canonical_titles_total", "canonical_verified",
      "canonical_title_status", "games_registered", "apps_registered", "root_causes_total")}, indent=1))
