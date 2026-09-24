#!/usr/bin/env python3
"""S-HYGIENE: S78 accidental-snapshot disposition ledger + safe rescue.

For every blob reachable ONLY from backup/s78-accidental-snapshot (absent from
main history):
  - rescue small knowledge/evidence files into docs/history/s78_quarantine_recovery/
    (in-repo) AND external_backup/s78_quarantine/ (on-disk, gitignored)
  - rescue larger obsolete-but-unique files into external_backup/ only
  - record EVERYTHING in a complete ledger manifest with SHA256 + disposition reason

Platform/toolchain fragment (platform-34.zip) is recorded (SHA) but not rescued:
deterministically re-obtainable via scripts/bootstrap_toolchain.sh.
"""
import hashlib
import json
import os
import subprocess
import sys

REPO = "/home/z/my-project"
SNAPSHOT = "d51f1815"          # unique accidental-snapshot commit (S78)
BASE = "c6d14d2e"              # S77 baseline (ancestor of main)
OUT_INREPO = os.path.join(REPO, "docs/history/s78_quarantine_recovery")
OUT_DISK = os.path.join(REPO, "external_backup/s78_quarantine")
MAX_INREPO_BYTES = 512 * 1024  # only files <=512KB go into the repo
# in-repo rescue restricted to knowledge/evidence trees + root knowledge files;
# raw sweep traces / probe outputs stay disk-only (§6: raw logs whose session
# report already holds the promoted facts are not repo content)
INREPO_PREFIXES = ("docs/",)
INREPO_ROOT_FILES = {"F023_ROOT_CAUSE.md", "PLAYABILITY_REPORT.md",
                     "MessageSchema.java", "delivery_bin.json"}
TOOLCHAIN_FILES = {"platform-34.zip"}

# dirs whose blobs are disposable classes per S78 report + artifact policy:
# workspace backups (gc_work), compiled binary (miniandroid_prof), inflated APK
# trees (apk_build — upstream source available, §12 SOURCE-AVAILABLE), corpus
# caches, agent state (hc_provenance), raw PPM captures + demo frames
# (superseded by canonical evidence).
DISPOSABLE_DIRS = (
    "gc_work/", "miniandroid_prof/", "apk_build/", "corpus_cache/",
    "hc_provenance/", "demo_frames_f076/", "demo_gif_new/", "miniandroid_ws/",
)


def git(*args, binary=False):
    r = subprocess.run(["git", "-C", REPO] + list(args), capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.decode()[:300]}")
    return r.stdout if binary else r.stdout.decode()


def main():
    # 1. blobs reachable from main (set)
    main_blobs = set()
    for line in git("rev-list", "--objects", "main").splitlines():
        if line:
            main_blobs.add(line.split(" ", 1)[0])

    # 2. full snapshot tree
    snap_entries = []  # (path, sha, size)
    for line in git("ls-tree", "-r", "--long", SNAPSHOT).splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        meta, path = line.split("\t", 1)
        f = meta.split()
        snap_entries.append((path, f[2], int(f[3])))

    ledger = {"rescued_inrepo": [], "rescued_disk_only": [],
              "disposed": [], "already_in_main": 0}
    for path, sha, size in sorted(snap_entries):
        if sha in main_blobs:
            ledger["already_in_main"] += 1
            continue
        rec = {"path": path, "blob_sha": sha, "bytes": size}
        if path in TOOLCHAIN_FILES:
            rec.update(disposition="DISPOSED_TOOLCHAIN",
                       reason="deterministically re-obtainable via scripts/bootstrap_toolchain.sh")
            ledger["disposed"].append(rec)
            continue
        if path.startswith(DISPOSABLE_DIRS):
            cls = path.split("/", 1)[0]
            reasons = {
                "gc_work": "workspace backup tree (S-era handoff zips already audited FULLY_REPRESENTED)",
                "miniandroid_prof": "compiled build binary (regenerable)",
                "apk_build": "inflated APK tree of open-source corpus apps — §12 SOURCE-AVAILABLE: upstream source supersedes reverse-engineering artifacts",
                "corpus_cache": "download cache (external-cache policy)",
                "hc_provenance": "agent runtime state",
                "demo_frames_f076": "raw capture frames superseded by canonical evidence",
                "demo_gif_new": "raw capture superseded by canonical evidence",
                "miniandroid_ws": "workspace backup zip (A-03 = FULLY_REPRESENTED by source-forensics audit)",
            }
            rec.update(disposition="DISPOSED", reason=reasons.get(cls, cls))
            ledger["disposed"].append(rec)
            continue
        # unique knowledge/evidence file -> rescue
        data = git("cat-file", "blob", sha, binary=True)
        sha256 = hashlib.sha256(data).hexdigest()
        rec["sha256"] = sha256
        disk_path = os.path.join(OUT_DISK, path)
        os.makedirs(os.path.dirname(disk_path), exist_ok=True)
        with open(disk_path, "wb") as fh:
            fh.write(data)
        if size <= MAX_INREPO_BYTES and (path.startswith(INREPO_PREFIXES)
                                         or path in INREPO_ROOT_FILES):
            inrepo_path = os.path.join(OUT_INREPO, path)
            os.makedirs(os.path.dirname(inrepo_path), exist_ok=True)
            with open(inrepo_path, "wb") as fh:
                fh.write(data)
            rec.update(disposition="RESCUED_INREPO+DISK")
            ledger["rescued_inrepo"].append(rec)
        else:
            rec.update(disposition="RESCUED_DISK_ONLY",
                       reason="raw run trace / superseded research data — kept on disk outside git (§6 raw-log law / superseded by canonical registries); not repo content")
            ledger["rescued_disk_only"].append(rec)

    os.makedirs(OUT_INREPO, exist_ok=True)
    manifest = {
        "schema": "miniandroid.s78_disposition.v1",
        "snapshot_commit": SNAPSHOT,
        "snapshot_base": BASE,
        "branch": "backup/s78-accidental-snapshot",
        "generated_by": "scripts/s_hygiene_s78_disposition.py",
        "policy": "every blob unique to the quarantined snapshot is either RESCUED (in-repo and/or external_backup with SHA256) or explicitly DISPOSED with a class reason; nothing is silently dropped",
        "ledger": ledger,
    }
    with open(os.path.join(OUT_INREPO, "MANIFEST.json"), "w") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)

    n_ri, n_rd, n_dis = len(ledger["rescued_inrepo"]), len(ledger["rescued_disk_only"]), len(ledger["disposed"])
    b_ri = sum(r["bytes"] for r in ledger["rescued_inrepo"])
    b_rd = sum(r["bytes"] for r in ledger["rescued_disk_only"])
    b_dis = sum(r["bytes"] for r in ledger["disposed"])
    print(f"snapshot files: {len(snap_entries)}  already-in-main: {ledger['already_in_main']}")
    print(f"RESCUED in-repo: {n_ri} files, {b_ri/1024:.0f}KB")
    print(f"RESCUED disk-only: {n_rd} files, {b_rd/1024:.0f}KB")
    print(f"DISPOSED (ledgered): {n_dis} blobs, {b_dis/1048576:.1f}MB")
    for r in sorted(ledger["disposed"], key=lambda r: -r["bytes"])[:8]:
        print(f"  disposed {r['bytes']/1048576:7.1f}MB {r['path'][:80]}")


if __name__ == "__main__":
    sys.exit(main())
