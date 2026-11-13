#!/usr/bin/env python3
"""duplicate_scan.py — byte-identical duplicate detection for evidence trees.

#587 forensic-addendum §7 law: "Detect byte-identical files by SHA and
fail/warn on new duplicates unless a documented reason exists."

Modes:
  census   (default) walk the given paths, group files by SHA-256, print
           groups with more than one member (count-only verdict, exit 0).
  strict   exit 1 when any duplicate group exists among the given paths and
           the path is not in the per-file exemption registry
           (docs/EVIDENCE_DUPLICATE_EXEMPTS.json: {path: reason}).

Repo-portable (root discovery from __file__); no machine-specific paths.
"""
import hashlib
import json
import os
import sys


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def duplicate_groups(paths):
    """Return {sha: [paths...]} for files with identical bytes."""
    by_sha = {}
    for p in iter_files(paths):
        try:
            by_sha.setdefault(sha256(p), []).append(p)
        except OSError:
            continue
    return {s: ps for s, ps in by_sha.items() if len(ps) > 1}


def iter_files(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
                for fn in files:
                    yield os.path.join(root, fn)
        elif os.path.isfile(p):
            yield p


def load_exempts():
    ex = os.path.join(repo_root(), "docs", "EVIDENCE_DUPLICATE_EXEMPTS.json")
    if os.path.exists(ex):
        with open(ex, encoding="utf-8") as f:
            return json.load(f)
    return {}


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    strict = "--strict" in argv
    if not args:
        print("usage: duplicate_scan.py [--strict] <path>...")
        return 2
    groups = duplicate_groups(args)
    n_files = sum(len(ps) for ps in groups.values())
    waste = sum(os.path.getsize(ps[0]) * (len(ps) - 1)
                for ps in groups.values() if ps)
    print(f"duplicate_scan: {len(groups)} duplicate group(s), "
          f"{n_files} file(s) involved, {waste} redundant bytes")
    exempts = load_exempts()
    unexempt = 0
    for s, ps in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        all_exempt = all(os.path.relpath(p, repo_root()) in exempts for p in ps)
        tag = " (exempt)" if all_exempt else ""
        if not all_exempt:
            unexempt += len(ps) - 1
        print(f"  {s[:16]} x{len(ps)}{tag}: "
              + "; ".join(os.path.relpath(p, repo_root()) for p in ps[:4])
              + (" ..." if len(ps) > 4 else ""))
    if strict and unexempt:
        print(f"strict: {unexempt} redundant path(s) without exemption")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
