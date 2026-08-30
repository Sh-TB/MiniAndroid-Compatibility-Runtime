#!/usr/bin/env python3
"""Build UNIFIED_007.zip — third-party usable release package.

Layout (charter §51):
  UNIFIED_007/
    README.md QUICKSTART.md ARCHITECTURE.md API.md status.json
    source/          (src, tools, api, scripts, tests, Makefile, .gitignore)
    build/           (STRIPPED miniandroid + exp124_golden_journey binaries)
    docs/            (campaign knowledge + FINAL_REPORT)
    evidence/        (arsc probe, journey_report, regression summaries,
                      tg regression sha, job api test output)
    screenshots/     (golden journey 7 + telegram regression)
    logs/            (journey stderr, regression logs, api test log)
    traces/          (journey api_trace sample)
    api/             (server.py, server_test.py, sample job.json)
    MANIFEST.sha256  (every file hashed)
Then VERIFY (§43): extract to tmp → rebuild from extracted source → run the
golden journey from extracted build → compare screenshot SHA-256 with the
original → run api tests → verify manifest.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "download", "miniandroid_unified_campaign"))
STAGE = os.path.join(OUT_DIR, "stage_unified_007")
ZIP_PATH = os.path.join(OUT_DIR, "UNIFIED_007.zip")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def add(st, rel_src, rel_dst, required=True):
    src = os.path.join(REPO, rel_src)
    dst = os.path.join(st, rel_dst)
    if not os.path.exists(src):
        if required:
            raise SystemExit(f"MISSING required file: {rel_src}")
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.isdir(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst,
                        ignore=shutil.ignore_patterns("*.o", "jobs", "*.d"))
    else:
        shutil.copy2(src, dst)


def main():
    if os.path.exists(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)
    root = os.path.join(STAGE, "UNIFIED_007")

    # top-level docs
    for f in ("README.md", "QUICKSTART.md", "ARCHITECTURE.md", "API.md",
              "status.json", ".gitignore"):
        add(root, f, f)
    # source
    for d in ("src", "tools", "tests", "scripts", "third_party"):
        add(root, d, f"source/{d}")
    add(root, "api/server.py", "api/server.py")
    add(root, "api/server_test.py", "api/server_test.py")
    add(root, "Makefile", "source/Makefile")
    # build: stripped binaries
    os.makedirs(os.path.join(root, "build"), exist_ok=True)
    for b in ("miniandroid", "exp124_golden_journey"):
        src = os.path.join(REPO, "build", b)
        dst = os.path.join(root, "build", b)
        subprocess.run(["cp", src, dst], check=True)
        subprocess.run(["strip", dst], check=True)
    # docs
    for f in ("docs/UNIFIED_007_FINAL_REPORT.md",):
        add(root, f, f)
    add(root, "docs", "docs", required=True)
    # evidence (curated, bounded)
    add(root, "run_exp007/arsc/summary.json", "evidence/arsc/summary.json")
    add(root, "run_exp007/arsc/verified_android_attrs.json",
        "evidence/arsc/verified_android_attrs.json")
    for name in sorted(os.listdir(os.path.join(REPO, "run_exp007/arsc"))):
        if name.endswith("_arsc.json"):
            add(root, f"run_exp007/arsc/{name}", f"evidence/arsc/{name}")
    add(root, "run_exp007/golden/journey_report.json",
        "evidence/golden/journey_report.json")
    add(root, "run_exp007/golden/journey_stderr.log",
        "logs/journey_stderr.log")
    for apk in ("gmdice", "dooz", "unote", "microtimer", "notes", "chessclock"):
        add(root, f"run_exp007/regress/{apk}.log",
            f"logs/regress_{apk}.log", required=False)
    # screenshots
    for f in sorted(os.listdir(os.path.join(REPO, "run_exp007/golden"))):
        if f.endswith(".png") and f != "screenshot.png":
            add(root, f"run_exp007/golden/{f}", f"screenshots/golden/{f}")
    add(root, "run_exp007/tg_regression/screenshot.png",
        "screenshots/telegram_regression.png")
    # logs + traces
    add(root, "run_exp007/tg_regression.log", "logs/tg_regression.log",
        required=False)
    add(root, "run_exp007/golden/api_trace.json", "traces/golden_api_trace.json",
        required=False)
    # api sample job
    jobs = os.path.join(REPO, "api", "jobs")
    if os.path.isdir(jobs):
        first = sorted(os.listdir(jobs))[0]
        add(root, f"api/jobs/{first}/job.json", "api/sample_job.json")
    # corpus note (APKs are NOT redistributed — sources documented)
    add(root, "tests/corpus/apks.json", "source/tests/corpus/apks.json")

    # MANIFEST
    manifest_lines = []
    for base, _, files in os.walk(root):
        for f in sorted(files):
            p = os.path.join(base, f)
            rel = os.path.relpath(p, root)
            manifest_lines.append(f"{sha256(p)}  {rel}")
    with open(os.path.join(root, "MANIFEST.sha256"), "w") as f:
        f.write("\n".join(manifest_lines) + "\n")

    # zip
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(root):
            for f in sorted(files):
                p = os.path.join(base, f)
                z.write(p, os.path.relpath(p, STAGE))
    print(f"zip built: {ZIP_PATH} ({os.path.getsize(ZIP_PATH)} bytes, "
          f"{len(manifest_lines)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
