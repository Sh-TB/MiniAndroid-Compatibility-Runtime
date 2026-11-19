#!/usr/bin/env python3
"""Emit the single authoritative MiniAndroid version/commit header (ISSUE-607 item 8).

The repository had three disagreeing identity strings (CHANGELOG v0.0.6.2,
README UNIFIED_011.1, code "v0.1"). This script is the ONE generated source of
truth: it reads the `VERSION` file plus the current Git commit and writes
`miniandroid_version.h` into the build directory (never the source tree).

Both build systems call it:
  * Makefile  -> build/generated/miniandroid_version.h
  * CMake     -> <binary-dir>/generated/miniandroid_version.h

The header exposes MINIANDROID_VERSION (the semantic version) and
MINIANDROID_COMMIT (the exact build commit), consumed by src/main.cpp and the
--version output so every artifact can be traced to a commit + version.
"""
import argparse
import os
import subprocess
import sys


def git_commit() -> str:
    """Return the exact HEAD commit SHA, or 'unknown' outside a Git checkout."""
    for key in ("MINIANDROID_COMMIT", "GIT_COMMIT"):
        val = os.environ.get(key)
        if val:
            return val.strip()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--version-file", required=True,
                    help="Path to the VERSION file (single source of truth)")
    ap.add_argument("--out", required=True,
                    help="Path of the generated miniandroid_version.h")
    ap.add_argument("--commit", default=None,
                    help="Override commit (defaults to git HEAD)")
    args = ap.parse_args()

    with open(args.version_file, "r", encoding="utf-8") as fh:
        version = fh.read().strip()
    if not version:
        print(f"error: empty version in {args.version_file}", file=sys.stderr)
        return 1

    commit = args.commit or git_commit()

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    contents = (
        "// GENERATED — do not edit. Source: VERSION + git HEAD.\n"
        "// Regenerate via scripts/generate_version_header.py (Makefile/CMake).\n"
        "#pragma once\n"
        f'#define MINIANDROID_VERSION "{version}"\n'
        f'#define MINIANDROID_COMMIT "{commit}"\n'
    )
    # Only rewrite on change so downstream rebuilds stay incremental.
    try:
        with open(args.out, "r", encoding="utf-8") as fh:
            if fh.read() == contents:
                return 0
    except OSError:
        pass
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(contents)
    return 0


if __name__ == "__main__":
    sys.exit(main())
