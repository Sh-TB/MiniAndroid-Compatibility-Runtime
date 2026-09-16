#!/usr/bin/env python3
"""S48 evidence-compaction: archive raw campaign exhaust out of the operational tree.

Law (S48 brief §7): source / tests / compact evidence / indexes / docs = permanent.
Raw run exhaust (stderr/stdout dumps, per-instruction traces, raw framebuffers)
= disposable or archival — NEVER silently deleted without provenance.

What this does
  1. Moves raw exhaust to an EXTERNAL archive root (/home/z/archive/miniandroid)
     preserving repo-relative paths. Nothing is deleted outright.
  2. Moves compact per-dir evidence (report.md / execution_summary.json /
     screenshot.png) of the GPG-092..095 session into docs/evidence/solved/
     so the operational tree keeps the permanent forensic record.
  3. Records SHA256 + size + reason for EVERY moved file into
     docs/evidence/ARCHIVE_MANIFEST.json (committed — provenance survives).

Run AFTER the regression battery finishes (it does not touch tracked files,
but a quiet tree keeps the run deterministic and reviewable).
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys

REPO = "/home/z/my-project"
ARCHIVE = "/home/z/archive/miniandroid"
GPG_SESSION_DOC = "docs/evidence/solved/gpg_092_095_session"
MANIFEST = os.path.join(REPO, "docs/evidence/ARCHIVE_MANIFEST.json")

REASON_STDERR = ("raw run exhaust (campaign stderr/stdout dump); per-run results "
                 "already compacted into report.md/registry entries; archived "
                 "for forensic recovery, removed from operational tree (S48)")
REASON_GPG_RAW = ("GPG-092..095 forensic-session raw trace; session ran on a "
                  "stale Sep-13 binary and its findings were subsumed by the "
                  "S40-S43 laws (reconcile a6c3042c); compact report retained "
                  "in docs/evidence/solved/, raw trace archived (S48)")
REASON_GPG_DEX = ("forensic input copy of dooz classes.dex; Dooz APK is "
                  "hash-pinned and the DEX re-derivable; archived per the "
                  "zero-binary-fixture law (S48)")
REASON_PROBE = ("one-shot lambda probe output; superseded; archived (S48)")
COMPACT_REASON = ("compact GPG-092..095 session evidence (report/summary/"
                  "screenshot) relocated from operational run paths into the "
                  "curated evidence tree (S48)")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tracked(pattern_dirs):
    out = subprocess.run(["git", "ls-files"] + pattern_dirs, cwd=REPO,
                         capture_output=True, text=True, check=True)
    return [p for p in out.stdout.split("\n") if p]


def classify_run_file(path):
    base = os.path.basename(path)
    if base.endswith(("_stderr.txt", "_stdout.txt")):
        return "archive"
    if "/gpg_" in path:
        # compact GPG leftovers under run/: report.md + screenshot.png
        return "compact"
    return "keep"


def classify_gpg_root(path):
    base = os.path.basename(path)
    if base == "classes.dex":
        return "archive"
    if base == "gpg_lambda_probe.out":
        return "archive"
    if base.endswith(".ppm"):
        return "archive"           # raw framebuffer duplicate of the PNG
    if base.endswith(".json") and "trace" in base:
        return "archive"           # api/opcode/method/heap/register/lifecycle traces
    if base in ("report.md", "execution_summary.json", "screenshot.png"):
        return "compact"
    if base.endswith(".json"):
        return "compact"           # small summaries, keep by default
    return "keep"


def session_of(run_path):
    name = os.path.basename(run_path)
    for pref in ("sttt", "m3c", "s26", "s33", "s34", "s35", "s36", "s37",
                 "s38", "s39", "s40", "s41", "s42", "s43", "s44", "s45"):
        if name.startswith(pref):
            return pref
    return name.split("_")[0] if "_" in name else "session"


def move(src_rel, dst_abs, entry_reason, issue, disposition, manifest):
    src_abs = os.path.join(REPO, src_rel)
    if not os.path.exists(src_abs):
        print(f"  ! missing on disk (index-only): {src_rel}")
        return 0
    os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
    digest = sha256(src_abs)
    size = os.path.getsize(src_abs)
    shutil.move(src_abs, dst_abs)
    manifest.append({
        "original_path": src_rel,
        "disposition": disposition,
        "path": os.path.relpath(dst_abs, REPO) if disposition.startswith("COMPACT") else dst_abs,
        "sha256": digest,
        "size": size,
        "reason": entry_reason,
        "issue": issue,
        "status": "ARCHIVED" if disposition == "ARCHIVED_EXTERNAL" else "COMPACTED",
    })
    return size


def main():
    dry = "--apply" not in sys.argv
    manifest = []
    # existing manifest entries are preserved (idempotent appends)
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            try:
                manifest = json.load(f).get("archived", [])
            except Exception:
                manifest = []

    archived_files = archived_bytes = compact_files = compact_bytes = 0

    # ---- 1. miniandroid/run raw exhaust --------------------------------
    run_files = tracked(["miniandroid/run/"])
    for rel in sorted(run_files):
        act = classify_run_file(rel)
        if act == "keep":
            continue
        if act == "archive":
            dst = os.path.join(ARCHIVE, rel)
            issue = session_of(rel)
            n = move(rel, dst, REASON_STDERR, issue, "ARCHIVED_EXTERNAL", manifest) if not dry else os.path.getsize(os.path.join(REPO, rel))
            archived_files += 1; archived_bytes += n
        else:  # compact: run/gpg_* reports
            d = os.path.basename(os.path.dirname(rel))
            dst = os.path.join(REPO, GPG_SESSION_DOC, "run_gpg", d, os.path.basename(rel))
            n = move(rel, dst, COMPACT_REASON, "GPG-092..095 session", "COMPACTED_TO_EVIDENCE", manifest) if not dry else os.path.getsize(os.path.join(REPO, rel))
            compact_files += 1; compact_bytes += n

    # ---- 2. root gpg_* dirs --------------------------------------------
    gpg_files = [p for p in tracked(["gpg_dooz_dex", "gpg_lambda_probe.out"] + sorted(
        d for d in os.listdir(REPO) if d.startswith("gpg_") and os.path.isdir(d)))
        if p.startswith("gpg_")]
    seen_dirs = set()
    for rel in sorted(gpg_files):
        d = rel.split("/")[0]
        if d == "gpg_lambda_probe.out":
            n = os.path.getsize(os.path.join(REPO, rel)) if os.path.exists(os.path.join(REPO, rel)) else 0
            if not dry:
                n = move(rel, os.path.join(ARCHIVE, rel), REASON_PROBE, "GPG-092..095 session",
                         "ARCHIVED_EXTERNAL", manifest)
            archived_files += 1; archived_bytes += n
            continue
        base = os.path.basename(rel)
        act = classify_gpg_root(rel)
        if act == "keep":
            continue
        if act == "archive":
            dst = os.path.join(ARCHIVE, rel)
            reason = REASON_GPG_DEX if base == "classes.dex" else REASON_GPG_RAW
            n = os.path.getsize(os.path.join(REPO, rel)) if os.path.exists(os.path.join(REPO, rel)) else 0
            if not dry:
                n = move(rel, dst, reason, "GPG-092..095 session", "ARCHIVED_EXTERNAL", manifest)
            archived_files += 1; archived_bytes += n
        else:
            dst = os.path.join(REPO, GPG_SESSION_DOC, "root_gpg", d, base)
            n = os.path.getsize(os.path.join(REPO, rel)) if os.path.exists(os.path.join(REPO, rel)) else 0
            if not dry:
                n = move(rel, dst, COMPACT_REASON, "GPG-092..095 session", "COMPACTED_TO_EVIDENCE", manifest)
            compact_files += 1; compact_bytes += n
        seen_dirs.add(d)

    if dry:
        print(f"DRY-RUN: would archive {archived_files} files "
              f"({archived_bytes/1048576:.1f} MB), compact {compact_files} files "
              f"({compact_bytes/1048576:.2f} MB)")
        return 0

    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    doc = {
        "created": "S48 2026-09-16",
        "law": "raw campaign exhaust archived externally; compact evidence is "
               "the source of truth; SHA256 provenance recorded per artifact",
        "archive_root": ARCHIVE,
        "archived": manifest,
    }
    with open(MANIFEST, "w") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)

    # stage the deletions/additions so the cleanup commit is explicit
    subprocess.run(["git", "add", "-A", "miniandroid/run", "gpg_dooz_dex",
                    "gpg_lambda_probe.out"] + [d for d in os.listdir(REPO)
                    if d.startswith("gpg_") and os.path.isdir(d)],
                   cwd=REPO, check=False)
    subprocess.run(["git", "add", GPG_SESSION_DOC, "docs/evidence/ARCHIVE_MANIFEST.json"],
                   cwd=REPO, check=False)

    print(f"ARCHIVED {archived_files} files ({archived_bytes/1048576:.1f} MB) -> {ARCHIVE}")
    print(f"COMPACTED {compact_files} files ({compact_bytes/1048576:.2f} MB) -> {GPG_SESSION_DOC}")
    print(f"manifest entries: {len(manifest)} -> {MANIFEST}")
    # empty dirs that only held raw traces are now gone
    for d in sorted(seen_dirs):
        p = os.path.join(REPO, d)
        if os.path.isdir(p) and not os.listdir(p):
            os.rmdir(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
