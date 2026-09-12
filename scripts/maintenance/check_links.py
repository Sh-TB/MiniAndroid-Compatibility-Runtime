#!/usr/bin/env python3
"""WAVE 9 verification — stale-reference scan + markdown link checker."""
import subprocess, os, re, sys

os.chdir("/home/z/my-project")

def tracked():
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True)
    return [l for l in out.stdout.splitlines() if l.strip()]

files = tracked()

# ---------- 1. stale old-path signatures ----------
STALE = [
    r"docs/campaign014_evidence",
    r"(?<![-\w])source_forensics/",
    r"evidence/20260911-",
    r"miniandroid/docs/",
    r"miniandroid/experiments/",
    r"miniandroid/research/",
    r"docs/demo/",
    r"(?<![-\w])demo/build", r"(?<![-\w])demo/src", r"(?<![-\w])demo/build_demo_apk\.sh",
    r"(?<![-\w])demo/validate_demo_proof\.sh",
    r"(?<![-\w])recovery/",
    r"golden/expected_(object_model|screenshot_info|view_tree)\.json",
    r"scripts/build_fixture_apk\.sh", r"scripts/run_test_battery\.sh",
    r"scripts/fetch_corpus\.py", r"scripts/package_release\.sh",
    r"miniandroid/DO_NOT_REINVENT", r"miniandroid/STUB_DEBT", r"miniandroid/TEST_MATRIX",
    r"miniandroid/START_HERE", r"miniandroid/status\.json", r"miniandroid/status_011_1",
    r"miniandroid/build_exp019", r"miniandroid/build_exp042",
    r"miniandroid/run_exp09[23]", r"miniandroid/run_telegram_test",
]
print("=== STALE SIGNATURE SCAN (tracked text files, excluding ledger) ===")
hits = 0
for f in files:
    if f.endswith((".png", ".dex", ".bin", ".ogg", ".ppm", ".wav")):
        continue
    if f == "docs/maintenance/worklog.md":   # append-only historical ledger
        continue
    try:
        txt = open(f, encoding="utf-8", errors="strict").read()
    except (UnicodeDecodeError, OSError):
        continue
    for pat in STALE:
        for m in re.finditer(pat, txt):
            line_no = txt[:m.start()].count("\n") + 1
            line = txt.splitlines()[line_no - 1].strip()[:120]
            print(f"{f}:{line_no}: {line}")
            hits += 1
print(f"stale hits: {hits}")

# ---------- 2. markdown relative link checker ----------
print("\n=== MARKDOWN LINK CHECK ===")
bad = 0
link_re = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
for f in files:
    if not f.endswith(".md"):
        continue
    try:
        txt = open(f, encoding="utf-8", errors="strict").read()
    except (UnicodeDecodeError, OSError):
        continue
    base = os.path.dirname(f)
    for m in link_re.finditer(txt):
        tgt = m.group(1)
        if tgt.startswith(("http://", "https://", "mailto:", "#", "data:")):
            continue
        path = tgt.split("#")[0]
        if not path:
            continue
        path = path.lstrip("/")
        cand = os.path.normpath(os.path.join(base, path))
        if not os.path.exists(cand):
            line_no = txt[:m.start()].count("\n") + 1
            print(f"BROKEN {f}:{line_no}: -> {tgt}")
            bad += 1
print(f"broken md links: {bad}")
