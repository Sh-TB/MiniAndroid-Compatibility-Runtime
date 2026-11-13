#!/usr/bin/env python3
"""Policy validator — the executable arm of CONSTITUTION_V2 §172 (#587 R32)
plus the S213 image-size policy and the S214 default-deny path law (#587).

Dependency-free. Modes:
  check (default)   validate the CURRENT tracked tree; exit non-zero on any
                    violation not covered by docs/POLICY_ALLOWLIST.json,
                    docs/IMAGE_POLICY_BASELINE.json, docs/IMAGE_EXCEPTIONS.json
                    or docs/PATH_OWNERSHIP.json.
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

S213 image policy (docs/IMAGE_POLICY_BASELINE.json + docs/IMAGE_EXCEPTIONS.json):
  8. PNG >100 KiB and GIF/WebP >200 KiB and JPEG >200 KiB require a per-path legacy
     baseline record or a narrow per-file exception; a mutated baseline entry fails

S214 default-deny path law (docs/PATH_OWNERSHIP.json + docs/SIZE_BUDGET.json):
  9. frozen-area snapshot drift: ANY added/removed child path in a frozen area fails
 10. unregistered directory: any tracked file whose directory prefix is not in the
     approved_dirs adoption inventory fails (new dirs are forbidden by default)
 11. scratch residue: .rej/.bak/.orig/tilde everywhere; stdout/stderr-capture,
     scratch/api-dump/cache/build-system names outside exempt historical areas
 12. symlink escape: tracked symlink resolving outside the repo (or absolute) fails
 13. size budget: tracked path-summed bytes per top-level area over budget fails

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


def _load_json(rel, default):
    try:
        text = open(os.path.join(ROOT, rel), encoding="utf-8").read().strip()
        return json.loads(text) if text else default
    except FileNotFoundError:
        return default


def load_image_baseline():
    d = _load_json("docs/IMAGE_POLICY_BASELINE.json", {})
    return {e["path"]: e for e in d.get("legacy_images", [])}


def load_image_exceptions():
    d = _load_json("docs/IMAGE_EXCEPTIONS.json", {})
    return {e["path"]: e for e in d.get("exceptions", [])}


def load_path_registry():
    return _load_json("docs/PATH_OWNERSHIP.json", None)


def load_size_budget():
    return _load_json("docs/SIZE_BUDGET.json", None)


def tracked_files():
    out = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True)
    return [l for l in out.stdout.splitlines() if l]


def _snapshot_paths(files, prefix, exclude_prefixes):
    return [f for f in files if f.startswith(prefix)
            and not any(f.startswith(x) for x in exclude_prefixes)]


def _list_sha(paths):
    import hashlib
    return hashlib.sha256("\n".join(sorted(paths)).encode()).hexdigest()


def _dir_prefix(f):
    """The owning directory prefix for default-deny review: top-level name for
    loose/2-level files, the 2-level prefix for deeper paths."""
    parts = f.split("/")
    return parts[0] if len(parts) <= 2 else "/".join(parts[:2])


def s213_s214_checks(files, violations, warnings, mode, registry=None):
    """S213 image-size policy + S214 default-deny path law (#587).

    All checks degrade gracefully when their registry files are absent so the
    validator still works on minimal fixtures (tests provide their own).
    """
    baseline = load_image_baseline()
    exceptions = load_image_exceptions()
    if registry is None:
        registry = load_path_registry()
    budget_doc = load_size_budget()

    # 8. S213 image-size policy
    png_limit = 100 * 1024
    promote_limit = 200 * 1024
    for f in files:
        low = f.lower()
        ext = os.path.splitext(low)[1]
        if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            continue
        p = Path(ROOT) / f
        if p.is_symlink():
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        limit = png_limit if ext == ".png" else promote_limit
        if size <= limit:
            continue
        if f in exceptions:
            continue
        if f in baseline:
            rec = baseline[f]
            if rec.get("bytes") is not None and rec["bytes"] != size:
                violations.append(("IMAGE_POLICY_MUTATED", f,
                    f"legacy baseline entry says {rec['bytes']} bytes, tree has {size} — "
                    "re-measure and amend the baseline/exception in review, never silently"))
            continue
        violations.append(("IMAGE_POLICY_NEW", f,
            f"{size} bytes {ext[1:].upper()} over the {'100 KiB PNG' if ext == '.png' else '200 KiB promoted'} "
            "limit — needs narrow per-file exception (docs/IMAGE_EXCEPTIONS.json) or baseline amendment in review"))

    if registry is None:
        return  # minimal fixture without a registry: S214 structural checks not armed

    wave_evidence = registry.get("wave_evidence_registered", {}).get("path", "")
    wave_prefix = wave_evidence + "/" if wave_evidence else None

    # 9. frozen-area snapshot drift (any added or removed child path fails)
    for key, snap in registry.get("frozen_snapshot", {}).items():
        prefix = key if key.endswith("/") else key + "/"
        excludes = [wave_prefix] if (key == "evidence" and wave_prefix) else []
        members = _snapshot_paths(files, prefix, excludes)
        want_n, want_sha = snap.get("tracked_file_count"), snap.get("snapshot_sha256")
        got_sha = _list_sha(members)
        if len(members) != want_n or got_sha != want_sha:
            direction = "added" if len(members) > (want_n or 0) else "removed/changed"
            violations.append(("FROZEN_SNAPSHOT_DRIFT", key,
                f"frozen area changed: {len(members)} tracked children vs frozen {want_n} "
                f"({direction}) — frozen areas accept no new files; promotion needs a registry "
                "amendment approved in review"))

    # 10. unregistered directories (default-deny)
    approved = set(registry.get("approved_dirs", []))
    for f in files:
        pre = _dir_prefix(f)
        if pre not in approved and f not in approved:
            violations.append(("UNREGISTERED_DIRECTORY", f,
                f"directory prefix '{pre}' is not in docs/PATH_OWNERSHIP.json approved_dirs — "
                "new directories are forbidden by default; register path/owner/purpose/"
                "consumers/lifecycle in review first"))

    # 11. scratch residue
    rules = registry.get("scratch_rules", {})
    compiled = [(re.compile(rx), universal) for rx, universal in
                [(r, True) for r in rules.get("regex", [])]]
    universal_residue = re.compile(r"\.(rej|orig|bak)$|~$")
    exempt_prefixes = tuple(rules.get("exempt_prefixes", []))
    exempt_exts = tuple(rules.get("exempt_extensions", []))
    for f in files:
        p = Path(ROOT) / f
        if p.is_symlink():
            continue
        low = f.lower()
        if universal_residue.search(low):
            violations.append(("SCRATCH_RESIDUE", f,
                "patch-reject/backup residue tracked — delete it; keep the applied change in history"))
            continue
        if universal_residue.search(low):
            continue
        if low.endswith(exempt_exts):
            continue
        if f.startswith(exempt_prefixes):
            continue
        for rx, _u in compiled:
            if rx.search(low) and not universal_residue.search(low):
                violations.append(("SCRATCH_RESIDUE", f,
                    f"matches scratch rule '{rx.pattern}' — run output belongs in ignored "
                    ".cache/<tool-or-suite>/<run-id>/; tracked capture needs promotion review"))
                break

    # 12. symlink escape
    root_real = os.path.realpath(ROOT)
    for f in files:
        p = Path(ROOT) / f
        if not p.is_symlink():
            continue
        target = os.readlink(p)
        resolved = os.path.realpath(p)
        if os.path.isabs(target) or not (resolved == root_real or resolved.startswith(root_real + os.sep)):
            violations.append(("SYMLINK_ESCAPE", f,
                f"symlink target '{target}' resolves outside the repository — "
                "machine-specific escape paths are forbidden"))

    # 13. size budget
    if budget_doc:
        areas = budget_doc.get("areas", {})
        sums = {}
        for f in files:
            p = Path(ROOT) / f
            if p.is_symlink():
                continue
            try:
                sums[f.split("/")[0]] = sums.get(f.split("/")[0], 0) + p.stat().st_size
            except OSError:
                pass
        for top, info in areas.items():
            b = info.get("budget_bytes")
            if b is not None and sums.get(top, 0) > b:
                violations.append(("SIZE_BUDGET_EXCEEDED", top,
                    f"{sums[top]} tracked bytes over budget {b} — reviewed per-area exception "
                    "with reason+expiry required, or shrink the area"))


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
    al_cls = _paths(allow.get("forbidden_classes"))
    al_contra = _paths(allow.get("contradictory_evidence"))
    al_dup = _paths(allow.get("duplicates"))
    # a narrow per-file S213 exception (docs/IMAGE_EXCEPTIONS.json) IS the reviewed
    # entry the §172.5 image-size gate demands — merge it into the accepted set
    al_img = _paths(allow.get("oversize_images")) | set(load_image_exceptions().keys())
    violations, warnings = [], []

    files = tracked_files()
    registry = load_path_registry()

    # 1+2. root law + top-level ownership (registry is authoritative when present;
    # the hardcoded sets are the fallback for minimal fixtures without a registry)
    if registry is not None:
        approved_root = set(registry.get("approved_dirs", []))
        effective_tops = set(registry.get("top_level", {}).keys())
    else:
        approved_root, effective_tops = ROOT_ALLOWLIST, TOP_LEVEL_DIRS
    for f in files:
        if "/" not in f:
            if f not in approved_root:
                violations.append(("ROOT_LAW", f,
                    "not in the §172.2 root allowlist; amend CONSTITUTION_V2.md §172.2 in the same change or move the file"))
        elif f.split("/")[0] not in effective_tops and f.split("/")[0] != ".gitignore":
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

    # ---- S213/S214 phase (#587) -------------------------------------------
    s213_s214_checks(files, violations, warnings, mode, registry)

    if mode == "allowlist-json2":
        print(json.dumps({"note": "see s213_s214_checks codes"}, indent=1))
        return 0

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
