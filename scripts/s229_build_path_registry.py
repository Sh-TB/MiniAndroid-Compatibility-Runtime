#!/usr/bin/env python3
"""S229 — generate docs/PATH_OWNERSHIP.json + docs/SIZE_BUDGET.json (#587 S214-WP2/WP3).

Builds the machine-readable default-deny registry from the CURRENT tracked tree:
  * top_level: curated per-area contract (owner/purpose/classes/lifecycle/review)
  * approved_dirs: every 2-level directory prefix tracked at adoption (default-deny
    for anything new) + pre-registered wave evidence path
  * frozen_snapshot: count + sha256 of the sorted tracked-path list for frozen areas
    (drift in either direction fails the validator)
  * run_output_routing: .cache/<tool-or-suite>/<run-id>/ (never tracked by default)
Deterministic; re-running with the same tree reproduces byte-identical output except
the recorded generated date.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("MINIANDROID_REPO_ROOT") or Path(__file__).resolve().parents[1])
GENERATED = "2026-11-13"
ADOPTION = "S229 (#587 S213/S214; owner-approved in the #587 closeout thread)"

FROZEN_TOP = {
    "audit": "historical audit dumps (s128); frozen",
    "campaigns": "historical campaign scratch; frozen",
    "reports": "historical wave reports; frozen",
    "research": "historical research notes; frozen",
    "hc_provenance": "historical run provenance (hello_color); frozen",
    "probe_store": "historical gate-A probe store; frozen",
    "plugins": "plugin artifact manifests/index; frozen",
    "evidence": "historical campaign evidence; FROZEN for new children — promotion is explicit review",
}
FROZED_SUB = ["docs/history"]

# wave evidence dir registered BEFORE creation (the S214 process demonstrated on itself)
WAVE_EVIDENCE = "evidence/s229_s213_s214"


def tracked():
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True)
    return [l for l in out.stdout.splitlines() if l]


def snapshot_sha(paths):
    return hashlib.sha256("\n".join(sorted(paths)).encode()).hexdigest()


def main():
    files = tracked()
    tops = {}
    for f in files:
        tops.setdefault(f.split("/")[0], []).append(f)

    # approved directory prefixes from the current tree:
    #   * every top-level name (loose + 2-level files live there)
    #   * every 2-level prefix that is an actual directory (contains deeper files)
    approved = set(tops.keys())
    for f in files:
        parts = f.split("/")
        if len(parts) >= 3:
            approved.add("/".join(parts[:2]))
    approved.add(WAVE_EVIDENCE)  # pre-registered before creation

    frozen = {}
    for key in list(FROZEN_TOP) + FROZED_SUB:
        prefix = key + "/"
        if key == "evidence":
            members = [f for f in files if f.startswith(prefix) and not f.startswith(WAVE_EVIDENCE + "/")]
        else:
            members = [f for f in files if f.startswith(prefix)]
        frozen[key] = {
            "lifecycle": "frozen — no new files, no new directories",
            "tracked_file_count": len(members),
            "snapshot_sha256": snapshot_sha(members),
            "basis": "sorted git ls-files list at adoption " + ADOPTION,
        }

    top_level = {}
    contracts = {
        ".agent": ("agent workflow pointers", "docs, policy", "maintained"),
        ".github": ("CI + templates (workflow files currently blocked by PAT scope — see docs/ci/)", "ci, docs", "maintained"),
        "audit": ("historical audit dumps", "frozen historical", "frozen"),
        "campaigns": ("historical campaign scratch", "frozen historical", "frozen"),
        "canonical": ("machine-readable registries + curated proof", "json, md, gif", "maintained"),
        "docs": ("human documentation incl. docs/evidence/canonical + docs/upstream + docs/ci", "md, json, yml, png, jpg, gif", "maintained"),
        "evidence": ("historical campaign evidence (transitional); NEW children forbidden by default", "frozen historical", "frozen"),
        "examples": ("first-party runnable examples", "source, build files", "maintained"),
        "fixtures": ("intentional minimal test inputs", "source, apk, assets", "maintained"),
        "games": ("first-party game source", "source", "maintained"),
        "hc_provenance": ("historical run provenance", "frozen historical", "frozen"),
        "library_ecosystem": ("metadata-only build-on-demand registry", "json, md", "maintained"),
        "miniandroid": ("runtime implementation + framework data + build + runtime tests", "c/cpp/h, makefiles, java, assets", "maintained"),
        "plugins": ("plugin manifests/index", "frozen historical", "frozen"),
        "probe_store": ("historical gate-A probe store", "frozen historical", "frozen"),
        "registry": ("legacy registry area, distinct contract only", "json", "legacy-frozen"),
        "reports": ("historical wave reports", "frozen historical", "frozen"),
        "research": ("historical research notes", "frozen historical", "frozen"),
        "scripts": ("maintained build/test/release/audit scripts", "py, sh, mk", "maintained"),
        "tests": ("maintained tests", "py, source", "maintained"),
        "third_party": ("vendored deps actually consumed", "libs, headers, debs", "maintained"),
        "tools": ("maintained developer tools", "py, sh", "maintained"),
        "upstream": ("pinned third-party source trees for source-first builds", "pinned sources", "maintained"),
    }
    for top, members in sorted(tops.items()):
        purpose, classes, lifecycle = contracts.get(top, ("undocumented — fails default-deny review", "unknown", "unregistered"))
        top_level[top] = {
            "owner": "release engineering",
            "purpose": purpose,
            "allowed_artifact_classes": classes,
            "lifecycle": lifecycle,
            "tracked_files": len(members),
            "tracked_bytes": sum((ROOT / m).stat().st_size for m in members
                                 if not os.path.islink(ROOT / m) and os.path.exists(ROOT / m)),
            "adopted": ADOPTION,
            "review_trigger": "any new 2-level prefix or budget breach",
        }

    registry = {
        "_meta": {
            "law": "#587 S214-WP2 default-deny path law + tools/policy_validator.py",
            "generated": GENERATED,
            "adopted": ADOPTION,
            "rules": [
                "new tracked directories are forbidden by default: any 2-level prefix not in approved_dirs fails",
                "frozen areas fail on ANY added or removed child path (snapshot drift)",
                "run outputs go to ignored .cache/<tool-or-suite>/<run-id>/; tracked run output requires promotion review",
                "exceptions are exact-path, owned, justified, expiring; no blanket folder/extension grandfathering",
                "approved_dirs is the adoption inventory, not a growth license: growth requires registry amendment in review",
            ],
        },
        "top_level": top_level,
        "approved_dirs": sorted(approved),
        "frozen_snapshot": frozen,
        "wave_evidence_registered": {
            "path": WAVE_EVIDENCE,
            "owner": "release engineering (#587 S213/S214 closeout)",
            "approved_in": "#587 closeout comment (S229 wave)",
            "expected_classes": "md, json, tsv, csv",
            "note": "registered BEFORE creation — the S214 approval process demonstrated on this wave's own evidence",
        },
        "run_output_routing": {
            "default": ".cache/<tool-or-suite>/<run-id>/ (gitignored, untracked)",
            "tracked_run_output": "forbidden without explicit promotion review",
            "promotion_requires": "APK/runtime commit, command, environment, run ID, claim, hashes, status",
        },
        "scratch_rules": {
            "regex": [
                r"\.(rej|orig|bak)$", r"~$",
                r"_out\d*\.txt$", r"(^|/)(stdout|stderr)\.[a-z0-9]+$",
                r"(^|/)scratch", r"(^|/)api_?dump", r"(^|/)cache/",
                r"\.(ninja|ninja_log)$", r"(^|/)\.ninja_log$", r"(^|/)CMakeCache\.txt$",
                r"(^|/)compile_commands\.json$",
            ],
            "exempt_prefixes": ["evidence/", "docs/history/", "audit/", "campaigns/", "reports/",
                                "research/", "hc_provenance/", "probe_store/", "plugins/",
                                "upstream/", "fixtures/", "docs/"],
            "exempt_extensions": [".py", ".sh", ".mk", ".cmake"],
            "note": ".rej/.bak/.orig residue fails EVERYWHERE including maintained areas; "
                    "stderr/stdout-style names only fail when they are not script sources",
        },
    }
    (ROOT / "docs" / "PATH_OWNERSHIP.json").write_text(json.dumps(registry, indent=1))

    # size budget: measured now + 10% headroom (min 1 MiB), per top-level
    budget = {
        "_meta": {
            "law": "#587 S214-WP3 per-area size budget",
            "generated": GENERATED,
            "adopted": ADOPTION,
            "rule": "tracked path-summed bytes per top-level area; exceeding budget fails the "
                    "validator unless a reviewed per-area exception records the reason+expiry; "
                    "budgets were set at adoption with 10% headroom",
        },
        "areas": {},
    }
    for top, info in sorted(top_level.items()):
        measured = info["tracked_bytes"]
        headroom = max(int(measured * 0.10), 1024 * 1024)
        budget["areas"][top] = {
            "measured_at_adopted": measured,
            "budget_bytes": measured + headroom,
            "headroom_bytes": headroom,
            "review_trigger": "any tracked addition pushing the area over budget",
        }
    (ROOT / "docs" / "SIZE_BUDGET.json").write_text(json.dumps(budget, indent=1))

    print("PATH_OWNERSHIP.json: %d top-level areas, %d approved dirs, %d frozen snapshots"
          % (len(top_level), len(approved), len(frozen)))
    print("SIZE_BUDGET.json: %d areas" % len(budget["areas"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
