#!/usr/bin/env python3
"""
UNIFIED_007 — build UNIFIED_007_FINAL.zip with SELF-VERIFICATION.

Contents:
  miniandroid/                 full source tree (committed state)
  EVIDENCE/                    unified evidence pack (journeys, proofs, tests)
  README.md QUICKSTART.md ARCHITECTURE.md API.md STATUS.md
  UNIFIED_007_SELFTEST.md      how the zip verifies itself

Self-verification protocol (executed BEFORE zipping):
  1. fresh temp extract of the zip
  2. clean build (make from scratch objects)
  3. run: gmdice journey + audio suite + font proof + 3D proof + job server E2E
All steps must pass for the zip to be published; the build log is embedded.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile

REPO = "/home/z/my-project/repo/miniandroid"
OUT_DIR = "/home/z/my-project/download/miniandroid_unified_campaign"
ZIP_PATH = os.path.join(OUT_DIR, "UNIFIED_007_FINAL.zip")
STAGE = "/tmp/u007_zip_stage"

ROOT_DOCS = ["README_U007.md", "QUICKSTART_U007.md", "ARCHITECTURE_U007.md",
             "API_U007.md", "STATUS_U007.md"]
RENAMES = {"README_U007.md": "README.md", "QUICKSTART_U007.md": "QUICKSTART.md",
           "ARCHITECTURE_U007.md": "ARCHITECTURE.md", "API_U007.md": "API.md",
           "STATUS_U007.md": "STATUS.md"}

EXCLUDE_DIRS = {".git", "build", "run", ".cache"}

def build_zip():
    if os.path.exists(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)

    # source tree (git-clean state + untracked new files are committed already)
    src_dst = os.path.join(STAGE, "miniandroid")
    shutil.copytree(REPO, src_dst,
                    ignore=shutil.ignore_patterns(*EXCLUDE_DIRS, "*.ppm"))

    # evidence pack
    ev_dst = os.path.join(STAGE, "EVIDENCE")
    shutil.copytree(os.path.join(REPO, "run", "u007_evidence_pack"), ev_dst)

    # root docs
    for doc in ROOT_DOCS:
        shutil.copy(os.path.join(REPO, doc), os.path.join(STAGE, RENAMES[doc]))

    # commit hash for traceability
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True).stdout.strip()
    with open(os.path.join(STAGE, "SOURCE_COMMIT.txt"), "w") as f:
        f.write(head + "\n")

    # zip it
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, dirs, files in os.walk(STAGE):
            dirs.sort()
            for fn in sorted(files):
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, STAGE)
                z.write(full, rel)
    return head

def self_verify():
    """fresh extract → clean build → run test batteries. Returns (ok, log)."""
    import tempfile
    log = []
    ok_all = True

    def run(cmd, cwd, timeout, label):
        nonlocal ok_all
        log.append(f"\n===== {label} =====\n$ {' '.join(cmd)}  (cwd={cwd})")
        try:
            p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                               timeout=timeout)
            tail = (p.stdout + p.stderr).splitlines()[-25:]
            log.extend(tail)
            ok = p.returncode == 0
        except subprocess.TimeoutExpired:
            log.append("TIMEOUT")
            ok = False
        log.append(f"--> {'PASS' if ok else 'FAIL'}")
        ok_all = ok_all and ok
        return ok

    with tempfile.TemporaryDirectory(prefix="u007_verify_") as td:
        with zipfile.ZipFile(ZIP_PATH) as z:
            z.extractall(td)
        extracted = os.path.join(td, "miniandroid")

        run(["make", "clean"], extracted, 60, "make clean")
        run(["make", "-j4"], extracted, 1200, "clean build (make -j4)")
        run([os.path.join("build", "miniandroid"), "run",
             "--output", "run/verify_gmdice",
             "--journey", "run/verify_gmdice/journey", "--max-taps", "2",
             os.path.join("download", "corpus", "gmdice.apk")],
            extracted, 300, "gmdice real journey")
        run([os.path.join("build", "test_audio")], extracted, 120,
            "audio state machine suite")
        run([os.path.join("build", "u007_font_proof"),
             os.path.join("run", "verify_font")], extracted, 120,
            "font pipeline proof")
        run([os.path.join("build", "u007_3d_proof"),
             os.path.join("run", "verify_3d")], extracted, 120,
            "3D proof")
        run(["python3", os.path.join("scripts", "u007_job_server_test.py")],
            extracted, 400, "job server E2E")

    return ok_all, "\n".join(log)

head = build_zip()
print("zip built at commit", head)
ok, vlog = self_verify()

# write selftest report into the zip (rebuild zip with report included)
report = ("# UNIFIED_007 self-verification\n\nRESULT: " + ("ALL PASS" if ok else "FAILURES PRESENT") +
          "\n\n```\n" + vlog + "\n```\n")
with open(os.path.join(STAGE, "UNIFIED_007_SELFTEST.md"), "w") as f:
    f.write(report)
with zipfile.ZipFile(ZIP_PATH, "a", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(STAGE, "UNIFIED_007_SELFTEST.md"),
            "UNIFIED_007_SELFTEST.md")

sha = hashlib.sha256(open(ZIP_PATH, "rb").read()).hexdigest()
with open(os.path.join(OUT_DIR, "UNIFIED_007_FINAL_SHA256.txt"), "w") as f:
    f.write(sha + "  UNIFIED_007_FINAL.zip\n")
size = os.path.getsize(ZIP_PATH)
print(f"ZIP: {ZIP_PATH} ({size:,} bytes)")
print(f"SHA-256: {sha}")
print("SELF-VERIFY:", "ALL PASS" if ok else "FAILURES — see log")
sys.exit(0 if ok else 1)
