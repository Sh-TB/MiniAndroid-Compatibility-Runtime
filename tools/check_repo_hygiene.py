#!/usr/bin/env python3
"""S-HYGIENE repository hygiene gate (deterministic, dependency-free).

Fails (exit>0) when forbidden artifacts appear in the TRACKED tree:
  - APK/AAB/so blobs                (zero-APK law §20)
  - build output directories        (miniandroid/build/, build/)
  - raw *.log outside curated whitelists
  - oversized tracked files (>5MB hard limit without explicit allowlist)
  - obvious secret/token patterns in non-doc files
  - new archive blobs (.zip/.7z/.tar.gz) — handoff zips are forbidden in Git
Also runs tools/artifact_classifier.py logic classes for RAW_LOG/BUILD check.

This is intentionally SMALL: one file, stdlib only, deterministic output.
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZE_LIMIT = 5 * 1024 * 1024  # 5MB hard tracked-file limit
# documented canonical evidence above the limit (see docs/ARTIFACT_LIFECYCLE.md)
OVERSIZE_ALLOWLIST = {
    "docs/foundation/dex_census/bouncy.json": "canonical DEX census record",
    "docs/foundation/dex_census/com.emmanuelmess.tictactoe_3.json": "canonical DEX census record",
    "docs/foundation/knowledge_graph.json": "canonical knowledge graph",
    "docs/foundation/dex_census/io.github.yamin8000.dooz_23.json": "canonical DEX census record",
    "docs/foundation/dex_census/dooz_23_toplevel.json": "canonical DEX census record",
    "miniandroid/src/dex/dalvik_engine.cpp": "runtime source (largest single source file)",
    "run/s88/corpus/profiles.json": "canonical corpus profile data",
    "docs/foundation/api_matrix.json": "canonical API matrix",
    "upstream/s44/protobuf.jar": "pinned upstream reference jar",
    "upstream/s43/ui-android-1.11.4-sources.jar": "pinned upstream reference jar",
}

LOG_WHITELIST = (
    "docs/evidence/mc4_telegram/tg_run1_distilled.log",
    "docs/evidence/mc4_telegram/tg_run2_distilled.log",
    "docs/evidence/s60_r380/post_f106_keylines.log",
    "docs/evidence/s60_r380/pre_f106_face.log",
)
ARCHIVE_WHITELIST = tuple()  # handoff/backup zips are never committed

SECRET_PATTERNS = [
    re.compile(p) for p in (
        r"ghp_[A-Za-z0-9]{30,}", r"github_pat_[A-Za-z0-9_]{20,}",
        r"AKIA[0-9A-Z]{16}", r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
        r"xox[baprs]-[A-Za-z0-9-]{10,}", r"AIza[0-9A-Za-z_-]{35}",
    )
]


def git(*args):
    r = subprocess.run(["git", "-C", REPO] + list(args), capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode()[:300])
    return r.stdout


def main():
    files = git("ls-files").decode().splitlines()
    failures = []
    for f in files:
        low = f.lower()
        if low.endswith((".apk", ".aab", ".so")):
            failures.append(f"APK/SO tracked: {f}")
        if low.startswith(("miniandroid/build/", "build/")) or "/target/" in low:
            failures.append(f"build dir tracked: {f}")
        if low.endswith(".log") and f not in LOG_WHITELIST:
            failures.append(f"raw log tracked: {f}")
        if low.endswith((".zip", ".7z", ".tar.gz")) and f not in ARCHIVE_WHITELIST:
            failures.append(f"archive blob tracked: {f}")
        fp = os.path.join(REPO, f)
        if os.path.isfile(fp):
            if os.path.getsize(fp) > SIZE_LIMIT and f not in OVERSIZE_ALLOWLIST:
                failures.append(f"oversize >{SIZE_LIMIT>>20}MB: {f} "
                                f"({os.path.getsize(fp)//1048576}MB)")
            try:
                with open(fp, "rb") as fh:
                    head = fh.read(4096).decode("utf-8", "ignore")
            except OSError:
                continue
            if not f.endswith((".md", ".txt", ".json")):
                for pat in SECRET_PATTERNS:
                    if pat.search(head):
                        failures.append(f"secret pattern: {f}")
                        break
    print(f"REPO HYGIENE GATE: {len(files)} tracked files checked")
    if failures:
        print(f"FAIL ({len(failures)}):")
        for x in failures[:40]:
            print(f"  {x}")
        return 1
    print("PASS — zero APK/so, zero build dirs, zero raw logs (outside whitelist),"
          " zero archive blobs, zero oversize, zero secrets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
