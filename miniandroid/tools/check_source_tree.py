#!/usr/bin/env python3
"""
EXP-083 Phase 39.7 — Source-tree purity checker.

Verifies that the MiniAndroid source tree does NOT contain unexpected:
    *.apk, *.aab, *.log, *.tmp, *.dmp, *.core,
    large *.png, large *.jpg, large *.webp,
    build objects, generated executables,
    ZIP archives, extracted APK directories.

Exits 0 if pure; exits 1 with a violation report otherwise.

Usage:
    python tools/check_source_tree.py [--strict]
    python tools/check_source_tree.py --tracked-only
    python tools/check_source_tree.py --json

REPO_ROOT is the directory containing the .git directory (i.e. the actual
project root, NOT the miniandroid/ subdirectory).

Add explicit exceptions via the ALLOWED_* sets below.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def find_repo_root() -> Path:
    """Walk up from this file to find the directory containing .git."""
    p = Path(__file__).resolve()
    for parent in [p.parent] + list(p.parents):
        if (parent / ".git").exists():
            return parent
    # Fallback: assume two levels up
    return p.parent.parent.parent


REPO_ROOT = find_repo_root()

# Hard limits — files above these are flagged
LARGE_PNG_BYTES = 250 * 1024           # 250 KB
LARGE_BINARY_BYTES = 1 * 1024 * 1024  # 1 MB
APK_LARGE_BYTES = 5 * 1024 * 1024      # 5 MB — anything larger should be LFS/external
APK_HUGE_BYTES  = 50 * 1024 * 1024    # 50 MB — GitHub soft warning threshold

# File extensions that are NEVER allowed in source tree
NEVER_ALLOWED_EXTS = {".log", ".tmp", ".dmp", ".core", ".swp", ".swo"}

# Directories to SKIP entirely (these are gitignored or unrelated to source purity)
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", ".cache", ".idea", ".vscode",
    "tool-results",
    "build_asan", "build_exp019", "build_exp042",
}

# Directories that exist ONLY as build/runtime output (skip in non-strict mode)
GENERATED_DIRS = {"build", "run"}

# Allowed locations for APK files (relative to REPO_ROOT)
ALLOWED_APK_DIRS = {
    "miniandroid/test_apks/exp043/",
    "miniandroid/test_apks/exp052/",
    "miniandroid/test_apks/exp031_5/",
    "miniandroid/test_apks/exp031_6/",
    "miniandroid/download/apks/",
    "miniandroid/download/exp027_real_apks/",
    "miniandroid/download/exp027_real_apks_old/",
    "miniandroid/download/exp037_real_apks/",
    "miniandroid/download/exp072_corpus/",
    "miniandroid/download/exp073_real_apps/",
    "miniandroid/download/exp076_corpus/",
    "miniandroid/download/exp038_telegram/",  # Telegram (location allowed; size still flagged)
}

# Allowed individual APK files (NOT in the dirs above)
ALLOWED_APK_FILES = {
    "miniandroid/test_apks/HelloWorld.apk",
    "miniandroid/download/tictactoe.apk",
    "miniandroid/download/random_unote.apk",
}

# Specifically FORBIDDEN files (regardless of path) — these must NEVER be tracked
FORBIDDEN_FILES = {
    "miniandroid/build/miniandroid",
    "miniandroid/build/miniandroid_megabatch",
    "miniandroid/build/miniandroid_test",
    "miniandroid/build_asan/miniandroid_asan",
    "miniandroid/tools/miniandroid_exp042",
    "miniandroid/reports/telegram_call_graph.json",
    "miniandroid/download/exp037_real_apks/fdroid_index_v2.json",
}

# Allowed large image fixtures (regression fixtures requiring pixel-exact comparison)
ALLOWED_LARGE_IMAGE_DIRS = {
    "miniandroid/golden/",
    "miniandroid/run/golden/",
    "miniandroid/run/archive/",
}


def to_rel(p: Path) -> str:
    """Return repo-root-relative path with forward slashes."""
    try:
        return str(p.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def is_in_allowed_dir(rel: str, allowed_dirs: set[str]) -> bool:
    return any(rel.startswith(d) for d in allowed_dirs)


def is_tracked(rel: str) -> bool:
    """Return True if path is tracked by Git."""
    r = subprocess.run(
        ["git", "ls-files", "--error-unmatch", rel],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    return r.returncode == 0


def check_source_tree(strict: bool = False, tracked_only: bool = False) -> list[dict]:
    """Walk the working tree, find violations."""
    violations = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if not strict:
            dirs[:] = [d for d in dirs if d not in GENERATED_DIRS]

        for fn in files:
            p = Path(root) / fn
            rel = to_rel(p)
            ext = p.suffix.lower()
            try:
                sz = p.stat().st_size
            except OSError:
                continue

            if tracked_only and not is_tracked(rel):
                continue

            # 1. NEVER_ALLOWED_EXTS
            if ext in NEVER_ALLOWED_EXTS:
                violations.append({
                    "rule": f"FORBIDDEN_EXT_{ext}",
                    "path": rel,
                    "size_bytes": sz,
                    "message": f"Extension {ext} is forbidden in source tree",
                })
                continue

            # 2. FORBIDDEN_FILES
            if rel in FORBIDDEN_FILES:
                violations.append({
                    "rule": "FORBIDDEN_FILE",
                    "path": rel,
                    "size_bytes": sz,
                    "message": f"File {rel} is explicitly forbidden (see docs/TEST_CORPUS_POLICY.md)",
                })
                continue

            # 3. APK files
            if ext == ".apk":
                if not (is_in_allowed_dir(rel, ALLOWED_APK_DIRS) or rel in ALLOWED_APK_FILES):
                    violations.append({
                        "rule": "APK_NOT_IN_ALLOWED_DIR",
                        "path": rel,
                        "size_bytes": sz,
                        "message": f"APK file outside allowed directories: {rel}",
                    })
                elif sz > APK_HUGE_BYTES:
                    violations.append({
                        "rule": "APK_TOO_LARGE_FOR_GIT",
                        "path": rel,
                        "size_bytes": sz,
                        "message": f"APK > 50 MB must use Git LFS / GitHub Release: {rel}",
                    })
                elif sz > APK_LARGE_BYTES and rel not in {
                    "miniandroid/download/exp038_telegram/Telegram.apk",
                }:
                    violations.append({
                        "rule": "APK_LARGE_REVIEW_NEEDED",
                        "path": rel,
                        "size_bytes": sz,
                        "message": f"APK > 5 MB — review whether to move to LFS/external: {rel}",
                    })

            # 4. AAB files
            if ext == ".aab":
                violations.append({
                    "rule": "AAB_IN_SOURCE_TREE",
                    "path": rel,
                    "size_bytes": sz,
                    "message": f"AAB files should not be in source tree: {rel}",
                })

            # 5. ZIP / JAR archives
            if ext in (".zip", ".jar"):
                if not rel.startswith("miniandroid/third_party/"):
                    violations.append({
                        "rule": "ARCHIVE_NOT_ALLOWED",
                        "path": rel,
                        "size_bytes": sz,
                        "message": f"Archive {ext} not allowed in source tree: {rel}",
                    })

            # 6. Object files / build artifacts
            if ext in (".o", ".obj", ".a", ".so", ".dylib", ".dll"):
                violations.append({
                    "rule": "BUILD_ARTIFACT_IN_SOURCE",
                    "path": rel,
                    "size_bytes": sz,
                    "message": f"Build artifact {ext} outside build/ directory: {rel}",
                })

            # 7. Executables / binaries (no extension, large)
            if ext == "" and p.suffix == "" and sz > LARGE_BINARY_BYTES:
                if os.access(p, os.X_OK):
                    violations.append({
                        "rule": "LARGE_EXECUTABLE_IN_SOURCE",
                        "path": rel,
                        "size_bytes": sz,
                        "message": f"Large executable ({sz} bytes) in source tree: {rel}",
                    })

            # 8. Large PNG / JPG / WEBP
            if ext in (".png", ".jpg", ".jpeg", ".webp"):
                if sz > LARGE_PNG_BYTES:
                    if not is_in_allowed_dir(rel, ALLOWED_LARGE_IMAGE_DIRS):
                        violations.append({
                            "rule": "LARGE_IMAGE_IN_SOURCE",
                            "path": rel,
                            "size_bytes": sz,
                            "message": f"Large image ({sz} bytes) outside golden/archive/: {rel}",
                        })

    return violations


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="Also scan build/ and run/ (normally skipped).")
    ap.add_argument("--tracked-only", action="store_true",
                    help="Only report violations on Git-tracked files.")
    ap.add_argument("--json", action="store_true",
                    help="Output violations as JSON.")
    args = ap.parse_args()

    violations = check_source_tree(strict=args.strict, tracked_only=args.tracked_only)

    if args.json:
        print(json.dumps({"violations": violations, "count": len(violations)}, indent=2))
    else:
        if violations:
            print(f"FAIL: {len(violations)} source-tree purity violation(s) found:")
            print()
            for v in violations:
                print(f"  [{v['rule']}] {v['path']}  ({v['size_bytes']} bytes)")
                print(f"      {v['message']}")
            sys.exit(1)
        else:
            print("OK: source tree is pure (no violations).")
            sys.exit(0)


if __name__ == "__main__":
    main()
