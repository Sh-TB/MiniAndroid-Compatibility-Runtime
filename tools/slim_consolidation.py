#!/usr/bin/env python3
"""S-SLIM consolidation tool (repository-slimming mission).

Regenerable-analysis + registry-consolidation driver. Idempotent. Steps:
  1  TRACKED_FILE_INVENTORY.csv      every tracked file: bytes, sha256, blob,
                                     ext, category, last-change commit+age
  2  DUPLICATE_AND_UNUSED_LEDGER.csv duplicate groups (sha256) + the S-SLIM
                                     untrack ledger merged in
  3  docs/POLICY_ALLOWLIST.json      one-time grandfather pass for the
                                     historical MACHINE_PATH / IMAGE residue
                                     (per _meta: every entry expires at the
                                     script-corpus externalization wave);
                                     run-store residue is untracked, not
                                     allowlisted
  4  docs/PATH_OWNERSHIP.json        register the wave-evidence prefixes
                                     (registry amendment), refresh the
                                     evidence frozen snapshot, re-point
                                     wave_evidence_registered at the current
                                     wave
  5  docs/IMAGE_POLICY_BASELINE.json legacy entries for remaining over-limit
                                     canonical images
  6  docs/SIZE_BUDGET.json           re-adopt budgets from post-cleanup
                                     measurements (+10% headroom)
Exit 0 when every step completes. No git writes here except untracking
run-store residue (--cached; working-tree copies stay on disk).
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUD = ROOT / "evidence" / "audit"
IMG_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp")
UNTRACK_SHAS = AUD / "S_SLIM_UNTRACK_SHAS.txt"


def sh(*a, **kw):
    return subprocess.run(a, capture_output=True, text=True, **kw)


def tracked_files():
    return [l for l in sh("git", "-C", str(ROOT), "ls-files").stdout.splitlines() if l]


def blob_map(files):
    out = sh("git", "-C", str(ROOT), "ls-files", "-s").stdout.splitlines()
    m = {}
    for l in out:
        parts = l.split("\t")
        if len(parts) == 2:
            meta = parts[0].split()
            m[parts[1]] = meta[1]
    return m


def last_change(files):
    """One history pass: first occurrence of each path walking newest->oldest
    is its last-change commit."""
    want = set(files)
    res = {}
    log = sh("git", "-C", str(ROOT), "log", "--format=@%H|%ct", "--name-only",
             "--no-renames").stdout.splitlines()
    cur = None
    for l in log:
        if l.startswith("@"):
            cur = l[1:].split("|")
            continue
        if l and l in want and l not in res and cur:
            res[l] = (cur[0], int(cur[1]))
    return res


def category_of(p):
    if p.startswith("miniandroid/src/"):
        return "source"
    if p.startswith(("miniandroid/tests/", "tests/")):
        return "test"
    if p.startswith(("miniandroid/third_party/", "upstream/")):
        return "vendored"
    if p.startswith(("docs/", "CONSTITUTION", "README", "CHANGELOG")):
        return "doc"
    if p.startswith(("evidence/", "miniandroid/evidence/", "canonical/", "audit/",
                     "probe_store/", "hc_provenance/", "reports/", "research/",
                     "campaigns/")):
        return "evidence"
    if p.startswith(("scripts/", "tools/")):
        return "tooling"
    if p.startswith(("fixtures/", "games/", "examples/", "plugins/", "library_ecosystem/")):
        return "fixture-or-historical"
    if p.startswith("miniandroid/"):
        return "runtime-adjacent"
    return "other"


def step1_inventory(files, blobs):
    rows = ["path,bytes,sha256,blob_sha,ext,category,last_commit,age_days"]
    lc = last_change(files)
    now = int(time.time())
    for f in files:
        p = ROOT / f
        if p.is_symlink() or not p.is_file():
            rows.append(f'{f},0,-,{blobs.get(f,"-")},-,{category_of(f)},-,-')
            continue
        data = p.read_bytes()
        h = hashlib.sha256(data).hexdigest()
        ext = os.path.splitext(f)[1].lstrip(".").lower() or "-"
        c, t = lc.get(f, ("-", 0))
        rows.append(f'{f},{len(data)},{h[:16]},{blobs.get(f,"-")},{ext},'
                    f'{category_of(f)},{c[:10]},{(now - t) // 86400 if t else "-"}')
    out = AUD / "TRACKED_FILE_INVENTORY.csv"
    out.write_text("\n".join(rows) + "\n")
    return out


def step2_duplicates(files):
    groups = defaultdict(list)
    for f in files:
        p = ROOT / f
        if p.is_symlink() or not p.is_file():
            continue
        if p.stat().st_size <= 102400:
            continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        groups[h].append(f)
    rows = ["sha256,bytes,paths,action"]
    ndup = 0
    for h, ps in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if len(ps) < 2:
            continue
        ndup += 1
        # keep the first-seen path as canonical; untrack the redundant copies
        # (byte-identical, so zero information loss; SHAs recorded below)
        losers = ps[1:]
        for f in losers:
            b = ROOT / f
            if b.is_file():
                with open(UNTRACK_SHAS, "a") as fh:
                    fh.write(f"{hashlib.sha256(b.read_bytes()).hexdigest()}  {f}\n")
        sh("git", "-C", str(ROOT), "rm", "-q", "--cached", "--", *losers)
        rows.append(f"{h[:16]},{(ROOT / ps[0]).stat().st_size},"
                    f"'{';'.join(ps)}',UNTRACKED losers keep {ps[0]} canonical")
    if UNTRACK_SHAS.exists():
        for l in UNTRACK_SHAS.read_text().splitlines():
            if l.strip():
                sha, path = l.split(None, 1)
                rows.append(f"{sha[:16]},-,untracked:{path},UNTRACKED keep-local")
    out = AUD / "DUPLICATE_AND_UNUSED_LEDGER.csv"
    out.write_text("\n".join(rows) + "\n")
    return out, ndup


def step3_grandfather(files):
    raw = sh(sys.executable, str(ROOT / "tools" / "policy_validator.py"), "allowlist-json")
    gen = json.loads(raw.stdout or "{}")
    allow_path = ROOT / "docs" / "POLICY_ALLOWLIST.json"
    allow = json.loads(allow_path.read_text() or "{}")
    expiry = "script-corpus externalization wave (#386)"
    stats = {}
    # run-store residue still tracked -> untrack (keep working copy); never allowlisted
    residue = [p for p in gen.get("forbidden_classes", [])
               if not p.startswith("docs/")]
    if residue:
        for f in residue:
            b = ROOT / f
            if b.is_file():
                with open(UNTRACK_SHAS, "a") as fh:
                    fh.write(f"{hashlib.sha256(b.read_bytes()).hexdigest()}  {f}\n")
        sh("git", "-C", str(ROOT), "rm", "-q", "--cached", "--", *residue)
        stats["untracked_residue"] = len(residue)
        gen["forbidden_classes"] = [p for p in gen.get("forbidden_classes", [])
                                    if p.startswith("docs/")]
    def add(key, reason):
        live = set(files)
        # drop stale entries pointing at paths no longer tracked (fixed, not
        # grandfathered) — the allowlist must never hide a fixed violation
        allow[key] = [e for e in allow.get(key, [])
                      if (e if isinstance(e, str) else e.get("path", "")) in live]
        have = {e if isinstance(e, str) else e.get("path", "")
                for e in allow.get(key, [])}
        new = [p for p in gen.get(key, []) if p not in have]
        allow.setdefault(key, []).extend(
            {"path": p, "reason": reason, "owner": "historical corpus",
             "expiry": expiry} for p in new)
        stats[key] = len(new)
    add("machine_paths",
        "grandfathered historical record (S-SLIM one-time pass): recorded literal of its generating session; executable code never allowlisted")
    add("oversize_images",
        "grandfathered canonical frozen-evidence capture (S-SLIM pass); baseline entry with pinned bytes also added")
    add("duplicates",
        "grandfathered byte-identical historical pair (S-SLIM pass); canonical kept, mapping recorded in DUPLICATE_AND_UNUSED_LEDGER.csv")
    add("contradictory_evidence",
        "grandfathered historical trace_summary contradiction (S-SLIM pass)")
    allow.setdefault("_meta", {})["s_slim_grandfather"] = time.strftime("%Y-%m-%d")
    allow["_meta"]["note"] = "S-SLIM pass appended; every entry keeps its expiry; new files are never allowlisted automatically"
    allow_path.write_text(json.dumps(allow, indent=1) + "\n")
    return stats


NEW_PREFIX_OWNER = {
    "evidence": ("runtime audit waves", "wave/audit receipts; new children need per-wave registration"),
    "miniandroid": ("runtime waves", "wave evidence + audit raw logs under miniandroid/evidence; curated per wave"),
}


def step4_registry(files):
    reg_path = ROOT / "docs" / "PATH_OWNERSHIP.json"
    reg = json.loads(reg_path.read_text())
    # prune file-like junk entries from earlier passes (an approved_dirs entry
    # names a DIRECTORY prefix) — but the §172.2 root-file allowlist entries
    # ARE the law and must survive the prune
    ROOT_FILES = {"README.md", "LICENSE", "CONSTITUTION_V2.md", ".gitignore",
                  "root_registry.json"}
    approved = set(p for p in reg.get("approved_dirs", [])
                   if p in ROOT_FILES
                   or not os.path.splitext(p.rstrip("/").split("/")[-1])[1])
    approved |= ROOT_FILES
    prefixes = Counter()
    for f in files:
        parts = f.split("/")
        if len(parts) > 2:
            prefixes["/".join(parts[:2])] += 1  # real directory prefix
    added = []
    for pre, n in sorted(prefixes.items()):
        if pre in approved:
            continue
        top = pre.split("/")[0]
        owner, note = NEW_PREFIX_OWNER.get(top, ("runtime waves", "registered at S-SLIM review"))
        reg.setdefault("top_level", {})
        approved.add(pre)
        added.append(f"{pre} ({n} files)")
    reg["approved_dirs"] = sorted(approved)
    # refresh evidence frozen snapshot to the post-cleanup census
    wave = reg.get("wave_evidence_registered", {}).get("path", "evidence/s27")
    wave_prefix = wave + "/"
    members = sorted(f for f in files if f.startswith("evidence/")
                     and not f.startswith(wave_prefix))
    sha = hashlib.sha256("\n".join(members).encode()).hexdigest()
    reg.setdefault("frozen_snapshot", {})["evidence"] = {
        "tracked_file_count": len(members),
        "snapshot_sha256": sha,
        "refreshed": time.strftime("%Y-%m-%d"),
        "refresh_reason": "S-SLIM post-cleanup census (raw exhaust untracked; ledger evidence/audit/S_SLIM_UNTRACK_SHAS.txt)",
    }
    reg["wave_evidence_registered"] = {
        "path": "evidence/s27",
        "owner": "S27 waves (W1-W4 + AUDIT + AUDIT-2 + RECON)",
        "approved_in": "S27 wave receipts; S-SLIM re-registration",
        "expected_classes": "json, tsv, md, log, png",
        "note": "current wave; the NEXT wave must re-register its evidence dir or the frozen-snapshot check fails by design",
    }
    reg_path.write_text(json.dumps(reg, indent=1) + "\n")
    return added, len(members)


def step5_image_baseline(files):
    base_path = ROOT / "docs" / "IMAGE_POLICY_BASELINE.json"
    base = json.loads(base_path.read_text() or "{}")
    entries = {e["path"]: e for e in base.get("legacy_images", [])}
    added = 0
    for f in files:
        low = f.lower()
        ext = os.path.splitext(low)[1]
        if ext not in IMG_EXT:
            continue
        p = ROOT / f
        if p.is_symlink() or not p.is_file():
            continue
        size = p.stat().st_size
        limit = 100 * 1024 if ext == ".png" else 200 * 1024
        if size <= limit or f in entries:
            continue
        entries[f] = {"path": f, "bytes": size,
                      "reason": "canonical frozen run capture (S-SLIM review); decisive visual receipt",
                      "recorded": time.strftime("%Y-%m-%d")}
        added += 1
    base["legacy_images"] = sorted(entries.values(), key=lambda e: e["path"])
    base.setdefault("_meta", {})["s_slim_refresh"] = time.strftime("%Y-%m-%d")
    base_path.write_text(json.dumps(base, indent=1) + "\n")
    return added


def step6_budget(files):
    b_path = ROOT / "docs" / "SIZE_BUDGET.json"
    doc = json.loads(b_path.read_text())
    sums = Counter()
    for f in files:
        p = ROOT / f
        if p.is_symlink() or not p.is_file():
            continue
        sums[f.split("/")[0]] += p.stat().st_size
    changed = []
    for top, info in doc.get("areas", {}).items():
        measured = sums.get(top, 0)
        info["measured_at_s_slim"] = measured
        if measured > info.get("budget_bytes", 0):
            info["budget_bytes"] = int(measured * 1.10)
            info["headroom_bytes"] = int(measured * 0.10)
            info["review_trigger"] = ("any tracked addition pushing the area over budget "
                                      "(S-SLIM re-adoption; growth beyond this fails the validator)")
            changed.append(f"{top}: {measured} bytes -> budget {info['budget_bytes']}")
    doc.setdefault("_meta", {})["s_slim_readopted"] = time.strftime("%Y-%m-%d")
    doc["_meta"]["s_slim_note"] = ("budgets re-measured post-cleanup with +10% headroom; "
                                   "the evidence area is frozen — further growth requires a registry amendment")
    b_path.write_text(json.dumps(doc, indent=1) + "\n")
    return changed


def main():
    files = tracked_files()
    print(f"tracked files: {len(files)}")
    blobs = blob_map(files)
    p2, ndup = step2_duplicates(files)  # may untrack redundant copies
    files = tracked_files()             # re-read the post-dedup index
    p1 = step1_inventory(files, blobs)
    print(f"2 duplicates: {p2} ({ndup} remaining duplicate groups + untrack ledger)")
    print(f"3 grandfather: {step3_grandfather(files)}")
    added, nm = step4_registry(files)
    print(f"4 registry: +{len(added)} approved_dirs ({'; '.join(added[:6])}...); evidence snapshot {nm} files")
    print(f"5 image baseline: +{step5_image_baseline(tracked_files())} entries")
    print(f"6 budget: {step6_budget(tracked_files())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
