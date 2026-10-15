#!/usr/bin/env python3
"""S-HYGIENE repository hygiene gate (deterministic, dependency-free).

Fails (exit>0) when forbidden artifacts appear in the TRACKED tree:
  - APK/AAB/so blobs                (zero-APK law §20)
  - build output directories        (miniandroid/build/, build/)
  - raw *.log outside curated whitelists
  - oversized tracked files (>5MB hard limit without explicit allowlist)
  - obvious secret/token patterns in non-doc files
  - new archive blobs (.zip/.7z/.tar.gz) — handoff zips are forbidden in Git
  - Python bytecode / __pycache__ paths (regenerated on import; S59 law)
  - generated .class files outside the two documented evidence/upstream
    allowances (S59 law — intentional fixtures ship as source + DEX)

This is intentionally SMALL: one file, stdlib only, deterministic output.

Policy agreement with the tracked tree (S59, #386 C22/C28):
  - The three tracked res.zip build intermediates and the redundant
    kotlinc-2.1.20.zip were removed from the tree (REGENERATE/DEDUPLICATE);
    ARCHIVE_WHITELIST stays EMPTY on purpose.
  - Pinned build-critical toolchain / compiler-distribution files are
    allowlisted below WITH provenance; their externalization is PENDING a
    clean-room bootstrap proof (#386 rule 5) and is tracked in
    docs/REPOSITORY_HYGIENE.md + the dependency manifest.
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
    "miniandroid/framework_res/resources.arsc": (
        "AOSP framework-res resource table — runtime base data, NOT APK-derived "
        "payload (S127 R-NEW-423 law: engine package-0x01 router + 1120 "
        "framework-res files committed; required by every APK resource resolve)"),
    "tools/r8/r8.jar": (
        "pinned upstream R8/D8 dex compiler build tool (Google, Apache-2.0) — "
        "required for canonical fixture builds; external-cache refetch recipe "
        "documented in ledger docs/history/final_campaign_phase1/"),
    # --- S59 additions: pinned build toolchain (provenance per entry; the
    # externalization decision is PENDING clean-bootstrap proof, #386 rule 5) ---
    "tools/toolchain/aapt2": (
        "pinned AOSP build-tools aapt2 binary (Google, Apache-2.0) — consumed by "
        "8+ probe-fixture build scripts (cont11/12/18/53/56/62/65, closeout); "
        "bootstrap recipe scripts/build/bootstrap_toolchain.sh"),
    "tools/toolchain/android-34.jar": (
        "pinned android-34 platform stubs jar (Google, Apache-2.0) — compile "
        "classpath for every probe fixture; byte-identical duplicate of "
        "tools/android-34/android-34.jar (same blob, deduplicated by Git)"),
    "tools/android-34/android-34.jar": (
        "pinned android-34 platform stubs jar (Google, Apache-2.0) — canonical "
        "location; duplicate path kept until consumers are re-pointed and a "
        "clean bootstrap is proven (#386 C24)"),
    "tools/toolchain/r8.jar": (
        "pinned R8/D8 dex compiler (Google, Apache-2.0) — d8/dex conversion for "
        "probe fixtures; refetch recipe in bootstrap_toolchain.sh"),
    "upstream/cont12_maven/kotlinc-dist/kotlinc/lib/kotlin-annotation-processing.jar": (
        "kotlinc 2.1.20 distribution jar (JetBrains, Apache-2.0) — extracted "
        "compiler distribution consumed by scripts/cont12_build_oracle.sh; "
        "original archive removed S59 (zero consumers)"),
    "upstream/cont12_maven/kotlinc-dist/kotlinc/lib/kotlin-compiler.jar": (
        "kotlinc 2.1.20 compiler jar (JetBrains, Apache-2.0) — same provenance"),
    "upstream/cont12_maven/kotlinc-dist/kotlinc/lib/kotlin-main-kts.jar": (
        "kotlinc 2.1.20 main-kts jar (JetBrains, Apache-2.0) — same provenance"),
}

LOG_WHITELIST = (
    "docs/evidence/mc4_telegram/tg_run1_distilled.log",
    "docs/evidence/mc4_telegram/tg_run2_distilled.log",
    "docs/evidence/s60_r380/post_f106_keylines.log",
    "docs/evidence/s60_r380/pre_f106_face.log",
)
ARCHIVE_WHITELIST = tuple()  # handoff/backup zips are never committed

# S59: generated .class files are forbidden outside these two documented
# allowances (forensic evidence blob record + upstream reference snapshot).
CLASS_ALLOWLIST_PREFIXES = (
    "docs/research/source-forensics/evidence/",
    "upstream/s44/",
)

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


def check(files, repo_root):
    """Check a list of tracked paths; returns list of failure strings.

    Split out of main() so tools/test_check_repo_hygiene.py can drive
    positive/negative cases against synthetic file lists without touching
    the real index (C28 checker self-test law)."""
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
        if "__pycache__/" in f or low.endswith(".pyc"):
            failures.append(f"python bytecode tracked: {f}")
        if low.endswith(".class") and not f.startswith(CLASS_ALLOWLIST_PREFIXES):
            failures.append(f"generated class tracked: {f}")
        fp = os.path.join(repo_root, f)
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
    return failures


def main():
    files = git("ls-files").decode().splitlines()
    failures = check(files, REPO)
    print(f"REPO HYGIENE GATE: {len(files)} tracked files checked")
    if failures:
        print(f"FAIL ({len(failures)}):")
        for x in failures[:40]:
            print(f"  {x}")
        return 1
    print("PASS — zero APK/so, zero build dirs, zero raw logs (outside whitelist),"
          " zero archive blobs, zero oversize (outside provenanced allowlist),"
          " zero python bytecode, zero generated classes (outside evidence"
          " allowance), zero secrets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
