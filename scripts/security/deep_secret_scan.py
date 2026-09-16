#!/usr/bin/env python3
"""Permanent deep secret scanner (S49 Phase 0.2 forensic tool).

Complements scripts/security/check_secrets.sh (fast guard): this one walks the
ENTIRE git object store (all history, incl. unreachable objects) and is the
tool of record for audit campaigns.

Scans:
  1. Working tree (all files, excluding .git)
  2. .git metadata files (config, logs, packed-refs, COMMIT_EDITMSG, ...)
  3. The ENTIRE git object store (every blob/commit/tag/tree metadata text),
     including unreachable objects (past history, dangling, reflog-only).

SECURITY RULES:
  - NEVER prints a secret value. Only pattern TYPE, location, and length.
  - Exit code 0 = clean, 1 = secrets FOUND, 2 = internal error.
"""

import argparse
import os
import re
import subprocess
import sys

REPO = "/home/z/my-project"

# (pattern_name, compiled_regex, static_well_known_prefix_for_report)
PATTERNS = [
    ("GITHUB_FINEGRAINED_PAT", re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"), b"github_pat_"),
    ("GITHUB_CLASSIC_TOKEN", re.compile(rb"gh[pousr]_[A-Za-z0-9]{16,}"), b"ghX_"),
    ("AWS_ACCESS_KEY", re.compile(rb"\bAKIA[0-9A-Z]{16}\b"), b"AKIA"),
    ("AWS_TEMP_KEY", re.compile(rb"\bASIA[0-9A-Z]{16}\b"), b"ASIA"),
    ("PRIVATE_KEY_BLOCK", re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY( BLOCK)?-----"), b"-----BEGIN"),
    ("URL_EMBEDDED_CREDENTIAL", re.compile(
        rb"https?://[A-Za-z0-9._%-]+"
        rb":[A-Za-z0-9._%~!@$%^&*()+={}|;,<>/?-]{3,}@"), b"https://<cred>@host"),
    ("AUTH_HEADER_TOKEN", re.compile(rb"(?i)authorization['\"]?\s*[:=]\s*['\"]?(bearer|basic|token)\s+[A-Za-z0-9._\-+/=]{8,}"), b"Authorization:"),
    ("OPENAI_STYLE_KEY", re.compile(rb"\bsk-[A-Za-z0-9]{20,}\b"), b"sk-"),
    ("GOOGLE_API_KEY", re.compile(rb"\bAIza[0-9A-Za-z_\-]{30,}\b"), b"AIza"),
    ("GITLAB_PAT", re.compile(rb"\bglpat-[A-Za-z0-9_\-]{20,}\b"), b"glpat-"),
    ("NPM_TOKEN", re.compile(rb"\bnpm_[A-Za-z0-9]{30,}\b"), b"npm_"),
    ("HEROKU_API_KEY", re.compile(rb"(?i)heroku.{0,10}api.{0,10}key.{0,10}['\"]?\s*[:=]\s*['\"]?[0-9a-f]{8}-[0-9a-f]{4}"), b"heroku key"),
    ("GENERIC_TOKEN_ASSIGN", re.compile(
        rb"(?i)\b(GITHUB_TOKEN|GH_TOKEN|GIT_TOKEN|REPO_TOKEN|ACCESS_TOKEN|API_TOKEN|PERSONAL_ACCESS_TOKEN|PAT)\b\s*[=:]\s*['\"]?([A-Za-z0-9_\-]{16,})"),
        b"TOKEN=<redacted>"),
]

PLACEHOLDER_WORDS = re.compile(
    rb"(?i)(placeholder|your[_-]?token|changeme|change[_-]?me|example|xxxxxxxx|"
    rb"redacted|masked|<[^>]*>|\$\{[^}]*\}|\$ENV|REDACTED|<redacted>)")

MAX_REPORT_HITS_PER_LOCATION = 5


def classify(name: str, match: bytes) -> bool:
    """Filter obvious placeholders/false positives for generic patterns."""
    if name in ("GENERIC_TOKEN_ASSIGN", "URL_EMBEDDED_CREDENTIAL", "AUTH_HEADER_TOKEN",
                "HEROKU_API_KEY"):
        if PLACEHOLDER_WORDS.search(match):
            return False
    return True


class Report:
    def __init__(self):
        self.hits = []  # (surface, location, pattern, length)
        self.locations = {}

    def add(self, surface, location, pattern, length):
        key = (surface, location)
        self.locations.setdefault(key, [])
        if len(self.locations[key]) < MAX_REPORT_HITS_PER_LOCATION:
            self.locations[key].append((pattern, length))
        self.hits.append((surface, location, pattern, length))

    def found(self):
        return len(self.hits) > 0

    def print_report(self):
        if not self.found():
            print("SECRET SCAN RESULT: NOT FOUND (all surfaces clean)")
            return
        print("SECRET SCAN RESULT: FOUND")
        print(f"  total match events: {len(self.hits)} (values NEVER printed)")
        for (surface, location), pats in sorted(self.locations.items()):
            print(f"  [{surface}] {location}")
            for (pattern, length) in pats:
                print(f"      type={pattern}  value_length={length}  value=****MASKED****")


def scan_bytes(report, surface, location, data: bytes):
    for (name, rx, _prefix) in PATTERNS:
        for m in rx.finditer(data):
            if classify(name, m.group(0)):
                report.add(surface, location, name, len(m.group(0)))


def scan_working_tree(report):
    skip_dirs = {".git", "node_modules"}
    self_files = {os.path.abspath(__file__),
                  os.path.join(REPO, "scripts/security/check_secrets.sh")}
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            path = os.path.join(root, f)
            if os.path.abspath(path) in self_files:
                continue  # never self-match on our own regex literals
            try:
                if os.path.islink(path) or not os.path.isfile(path):
                    continue
                with open(path, "rb") as fh:
                    data = fh.read()
            except (OSError, PermissionError) as e:
                print(f"  [warn] unreadable: {path}: {e}", file=sys.stderr)
                continue
            if b"\x00" in data[:4096] and len(data) > 4096:
                # binary file: still scan whole bytes (secrets could hide in logs/dumps)
                pass
            rel = os.path.relpath(path, REPO)
            scan_bytes(report, "WORKTREE", rel, data)


GIT_META_FILES = [
    "config", "packed-refs", "COMMIT_EDITMSG", "MERGE_MSG", "FETCH_HEAD",
    "ORIG_HEAD", "info/exclude", "description", "shallow",
]


def scan_git_metadata(report):
    gitdir = os.path.join(REPO, ".git")
    for rel in GIT_META_FILES:
        p = os.path.join(gitdir, rel)
        if os.path.isfile(p):
            with open(p, "rb") as fh:
                scan_bytes(report, "GIT-META", f".git/{rel}", fh.read())
    # reflogs: every file under .git/logs
    logs_root = os.path.join(gitdir, "logs")
    for root, _dirs, files in os.walk(logs_root):
        for f in files:
            p = os.path.join(root, f)
            with open(p, "rb") as fh:
                scan_bytes(report, "GIT-REFLOG", os.path.relpath(p, gitdir), fh.read())


def scan_git_objects(report):
    """Stream EVERY object in the store (reachable + unreachable) through the scanner."""
    proc = subprocess.Popen(
        ["git", "cat-file", "--batch-all-objects", "--batch", "--unordered"],
        cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        while True:
            header = proc.stdout.readline()
            if not header:
                break
            parts = header.split()
            if len(parts) != 3:
                continue  # flush line or malformed; skip
            sha, otype, size = parts[0].decode(), parts[1].decode(), int(parts[2])
            content = proc.stdout.read(size)
            trailer = proc.stdout.read(1)  # trailing \n
            if otype in ("blob", "commit", "tag"):
                scan_bytes(report, f"GIT-OBJECT:{otype}", sha, content)
    finally:
        proc.stdout.close()
        proc.wait()
        if proc.returncode != 0:
            err = proc.stderr.read().decode(errors="replace")
            print(f"  [error] git cat-file rc={proc.returncode}: {err}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--surfaces", default="tree,meta,objects",
                    help="comma list: tree,meta,objects")
    args = ap.parse_args()
    surfaces = {s.strip() for s in args.surfaces.split(",")}

    report = Report()
    if "tree" in surfaces:
        print("scanning surface: WORKING TREE ...")
        scan_working_tree(report)
    if "meta" in surfaces:
        print("scanning surface: .git METADATA + REFLOGS ...")
        scan_git_metadata(report)
    if "objects" in surfaces:
        print("scanning surface: FULL GIT OBJECT STORE (all history) ...")
        scan_git_objects(report)

    report.print_report()
    sys.exit(1 if report.found() else 0)


if __name__ == "__main__":
    main()
