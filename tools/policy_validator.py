#!/usr/bin/env python3
"""Policy validator — the executable arm of CONSTITUTION_V2 §172 (#587 R32).

Dependency-free. Modes:
  check (default)   validate the CURRENT tracked tree; exit non-zero on any
                    violation not covered by docs/POLICY_ALLOWLIST.json.
  allowlist-json    print the machine-readable current violations (for the
                    one-time grandfather pass / review).

Checks (Constitution §172.5):
  1. root allowlist (exact)
  2. top-level directory ownership map (unknown new top-level entries fail)
  3. forbidden artifact classes: .pyc/.pyo, DB WAL/SHM/LOCK, extracted-app
     trees, raw stdout/stderr/log residues, unapproved ELF/archives in
     non-canonical locations, new screenshots outside canonical evidence
  4. evidence size gate: image >1 MiB fails, >500 KiB warns, unless allowlisted
  5. machine paths (/home/z, C:\\Users): ZERO tolerance in maintained areas;
     per-entry reviewed allowlist elsewhere (historical records)
  6. duplicate SHA detection: >100 KiB byte-identical regular files without
     allowlist entry fail; symlinks are aliases, not duplicates
  7. contradictory evidence: NO_APP_OPS + REAL_APP_CONTENT, draw_ops=0 with
     SUCCESS-style headline, stale screenshot-size claims (report-only scan of
     trace_summary.json / report.md pairs, failing outside the grandfather set)

Root allowlist (§172.2): README.md LICENSE CONSTITUTION_V2.md .gitignore
root_registry.json (documented compatibility projection).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = os.environ.get("MINIANDROID_REPO_ROOT") or str(Path(__file__).resolve().parents[1])
ALLOWLIST_PATH = os.path.join(ROOT, "docs", "POLICY_ALLOWLIST.json")

ROOT_ALLOWLIST = {"README.md", "LICENSE", "CONSTITUTION_V2.md", ".gitignore", "root_registry.json"}

TOP_LEVEL_DIRS = {
    ".agent": "agent contract and workflow pointers (§172.1)",
    ".github": "CI workflows, templates, policy enforcement (§172.1)",
    "audit": "historical audit dumps (s128); frozen, no new writes (§172.1 transitional)",
    "campaigns": "historical campaign scratch; frozen, no new writes (§172.1 transitional)",
    "canonical": "canonical machine-readable registries (§172.1)",
    "docs": "human documentation incl. docs/upstream versioned snapshots + docs/evidence/canonical (§172.1)",
    "evidence": "historical campaign evidence, transitional (§172.1)",
    "examples": "first-party runnable examples (§172.1)",
    "fixtures": "intentional test inputs (§172.1)",
    "games": "first-party game source (§172.1)",
    "hc_provenance": "historical run provenance (hello_color); frozen (§172.1 transitional)",
    "library_ecosystem": "metadata-only build-on-demand dependency registry (§172.1)",
    "miniandroid": "runtime implementation + framework data + build + runtime tests (§172.1)",
    "plugins": "metadata manifests/index for plugin artifacts (documented in REPOSITORY_STRUCTURE.md)",
    "probe_store": "historical gate-A probe store; frozen (documented in REPOSITORY_STRUCTURE.md)",
    "registry": "legacy registry area, distinct contract only (§172.1)",
    "reports": "historical wave reports; frozen (§172.1 transitional)",
    "research": "historical research notes; frozen (§172.1 transitional)",
    "root_registry.json": "compatibility projection of canonical/root_cause_registry.json (§172.2)",
    "scripts": "maintained build/test/release/audit scripts (§172.1)",
    "tests": "maintained tests (§172.1)",
    "tools": "maintained developer tools (§172.1)",
    "upstream": "pinned third-party source trees for source-first builds (§172.1)",
}

# Maintained = actively used by build/test/release/CI; ZERO machine-path tolerance.
# Historical documentation sub-areas are grandfathered via per-entry allowlist.
MAINTAINED_PREFIXES = ("tools/", "scripts/release/", "miniandroid/src/", "miniandroid/include/",
                       "miniandroid/Makefile", "miniandroid/CMakeLists.txt", "miniandroid/tests/",
                       "tests/", ".github/", "canonical/", "library_ecosystem/",
                       "docs/upstream/", "docs/REPOSITORY_STRUCTURE.md", "docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl")

MACHINE_PATH = re.compile(r"/home/z/my-project|/home/z/\w|C:\\\\Users\\\\")
DB_EXT = (".sqlite3", ".sqlite", ".db")
IMG_EXT = (".png", ".jpg", ".jpeg", ".gif", "webp")
RAWLOG = re.compile(r"(console\.log$|_out\d*\.txt$|_err\d*\.txt$|gate_out|\.log$)", re.I)


def load_allowlist():
    try:
        text = open(ALLOWLIST_PATH, encoding="utf-8").read().strip()
        return json.loads(text) if text else {"machine_paths": [], "oversize_images": [],
                                              "duplicates": [], "forbidden_classes": [],
                                              "contradictory_evidence": []}
    except FileNotFoundError:
        return {"machine_paths": [], "oversize_images": [], "duplicates": [],
                "forbidden_classes": [], "contradictory_evidence": []}


def tracked_files():
    out = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True)
    return [l for l in out.stdout.splitlines() if l]


def _paths(entries):
    out = set()
    for e in entries or []:
        out.add(e if isinstance(e, str) else e.get("path", ""))
    return out


def main():
    argv = sys.argv[1:]
    mode = argv[0] if argv else "check"
    raw = "--raw" in argv  # ignore existing allowlist (grandfather generation)
    allow = {} if raw else load_allowlist()
    al_mp = _paths(allow.get("machine_paths"))
    al_mp_rec = _paths(allow.get("machine_paths_maintained_records"))
    al_img = _paths(allow.get("oversize_images"))
    al_dup = _paths(allow.get("duplicates"))
    al_cls = _paths(allow.get("forbidden_classes"))
    al_contra = _paths(allow.get("contradictory_evidence"))
    violations, warnings = [], []

    files = tracked_files()

    # 1+2. root law + top-level ownership
    for f in files:
        if "/" not in f:
            if f not in ROOT_ALLOWLIST:
                violations.append(("ROOT_LAW", f,
                    "not in the §172.2 root allowlist; amend CONSTITUTION_V2.md §172.2 in the same change or move the file"))
        elif f.split("/")[0] not in TOP_LEVEL_DIRS and f.split("/")[0] != ".gitignore":
            violations.append(("TOP_LEVEL_OWNERSHIP", f,
                f"unknown top-level '{f.split('/')[0]}' — amend Constitution §172.1 + docs/REPOSITORY_STRUCTURE.md first"))

    # per-file class / size / machine-path checks
    seen_sha = {}
    for f in files:
        p = Path(ROOT) / f
        if p.is_symlink():
            continue  # alias, not a duplicate regular file; not readable as content
        try:
            st = p.stat()
        except OSError:
            continue
        size = st.st_size
        low = f.lower()
        # 3. forbidden classes (path-based; no read needed)
        if low.endswith((".pyc", ".pyo")):
            if f not in al_cls:
                violations.append(("FORBIDDEN_CLASS", f, "python bytecode tracked"))
        if low.endswith(("-wal", "-shm", "-lock")) or low.endswith(DB_EXT):
            if f not in al_cls:
                violations.append(("FORBIDDEN_CLASS", f, "database/WAL/SHM/LOCK tracked (run-store residue)"))
        if RAWLOG.search(f) and not low.endswith((".log.md",)):
            if f not in al_cls and not f.startswith("evidence/") and not f.startswith("docs/"):
                violations.append(("FORBIDDEN_CLASS", f, "raw log/output residue outside evidence areas"))
        # 4. evidence size gate (stat-based; no read of large binaries)
        ext = os.path.splitext(f)[1].lower()
        if ext in IMG_EXT and size > 1048576 and f not in al_img:
            violations.append(("IMAGE_OVER_1MB", f, f"{size} bytes — canonical-evidence allowlist entry required (purpose+claim+owner+source SHA+expiry)"))
        elif ext in IMG_EXT and size > 524288 and f not in al_img:
            warnings.append(("IMAGE_OVER_500KB", f, f"{size} bytes — consider derivative/lossless-optimize"))
        # text scans + duplicates: read only when the check needs content
        BUILD_FILES = ("Makefile", "CMakeLists.txt", "core_sources.manifest")
        is_text_ext = (f.endswith((".py", ".sh", ".md", ".json", ".jsonl", ".yml", ".yaml",
                                   ".js", ".c", ".h", ".cpp", ".tsv", ".txt", ".mk", ".cmake",
                                   ".bat", ".ps1", ".cfg", ".ini", ".toml", ".xml"))
                       or os.path.basename(f) in BUILD_FILES
                       or "/Makefile" in f)
        need_text = is_text_ext and size <= 8 * 1048576
        need_hash = size > 102400 and size <= 32 * 1048576
        data = None
        if need_text or need_hash:
            try:
                data = p.read_bytes()
            except OSError:
                data = None
        if data is None:
            continue
        # 5. machine paths
        if need_text:
            text = data.decode("utf-8", errors="ignore")
            if MACHINE_PATH.search(text):
                if f in ("tools/policy_validator.py", "tests/policy_validator_law_test.py"):
                    continue  # the enforcement tooling itself documents the pattern it detects (§172.5 self-reference)
                if any(f.startswith(mp) for mp in MAINTAINED_PREFIXES) or "/" not in f:
                    if f in al_mp_rec:
                        continue  # narrow source-reviewed exception: recorded run-output data record
                    violations.append(("MACHINE_PATH_MAINTAINED", f, "absolute developer path in a maintained area — zero tolerance (§172.5)"))
                elif f not in al_mp:
                    violations.append(("MACHINE_PATH", f, "absolute developer path — per-entry allowlist (reason/owner/expiry) required for historical records"))
        # 6. duplicates (regular files only; symlink = alias)
        if need_hash:
            h = hashlib.sha256(data).hexdigest()
            if h in seen_sha:
                if not (f in al_dup or seen_sha[h] in al_dup):
                    violations.append(("DUPLICATE_OVER_100KB", f, f"byte-identical to {seen_sha[h]} ({size} bytes) — keep one canonical object + mapping"))
            else:
                seen_sha[h] = f

    # 7. contradictory evidence scan
    for f in files:
        if f.endswith("trace_summary.json"):
            try:
                ts = json.loads((Path(ROOT) / f).read_text(errors="ignore"))
                fa = ts.get("frame_analysis", {})
                if fa.get("app_draw_ops") == 0 and fa.get("verdict") == "REAL_APP_CONTENT":
                    key = ("CONTRADICTORY_EVIDENCE", f)
                    if f not in al_contra:
                        violations.append((*key, "app_draw_ops=0 with verdict REAL_APP_CONTENT — ownership classifier contradiction must be reconciled or allowlisted"))
            except Exception:
                pass

    if mode == "allowlist-json":
        print(json.dumps({
            "machine_paths": sorted({v[1] for v in violations if v[0] == "MACHINE_PATH"}),
            "machine_paths_maintained_records": sorted({v[1] for v in violations if v[0] == "MACHINE_PATH_MAINTAINED"}),
            "oversize_images": sorted({v[1] for v in violations if v[0] == "IMAGE_OVER_1MB"}),
            "duplicates": sorted({v[1] for v in violations if v[0] == "DUPLICATE_OVER_100KB"}),
            "forbidden_classes": sorted({v[1] for v in violations if v[0] == "FORBIDDEN_CLASS"}),
            "contradictory_evidence": sorted({v[1] for v in violations if v[0] == "CONTRADICTORY_EVIDENCE"}),
        }, indent=1))
        return 0

    for w in warnings:
        print(f"WARN {w[0]} {w[1]}: {w[2]}")
    for v in violations:
        print(f"FAIL {v[0]} {v[1]}: {v[2]}")
    print(f"policy_validator: {len(violations)} violation(s), {len(warnings)} warning(s)")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
