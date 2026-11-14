#!/usr/bin/env python3
"""S235-0: append the local-only-artifacts ignore section to .gitignore.

Fixes the recurring session-boundary sweep: harness auto-commits (UUID
messages b110be50, bff51d90) twice swept 1556 untracked local files into the
tree. The sweep respects .gitignore (plain .so and .env were skipped), so an
ignore section durably stops it. Tracked files are never untracked by
gitignore, so already-promoted curated evidence stays tracked.
"""
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
GITIGNORE = BASE / ".gitignore"
PRE = "cfba2f41"  # last deliberate commit (S234-3) == origin/main

def sh(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True, cwd=BASE,
                          check=True).stdout

# 1. evidence subdirs that carry untracked run artifacts per the sweep commit
swept = sh("git", "show", "--name-only", "--format=", "HEAD").splitlines()
ev_dirs = sorted({l.split("/")[1] for l in swept if l.startswith("evidence/")})
# guard: never list a dir that is fully tracked on origin (nothing untracked)
lines, skipped = [], []
for d in ev_dirs:
    tracked = sh("git", "ls-tree", "-r", "--name-only", PRE,
                 f"-- evidence/{d}").strip()
    if tracked:
        lines.append(f"/evidence/{d}/")
    else:
        skipped.append(d)

section = """
# =============================================================================
# LOCAL-ONLY SESSION ARTIFACTS (2026-11-14, the S235-0 boundary-sweep fix)
# ---------------------------------------------------------------------------
# Incident: session-boundary auto-commits (UUID messages b110be50, bff51d90)
# twice swept 1556 untracked local files into the tree: 45 MB of OSMesa vendor
# blobs (three libOSMesa copies + the .deb packages), 0-byte PNG evidence,
# forensic raw data, reference dumps and historical run-store internals from
# pre-S230 sessions. The repository stays SOURCE + curated evidence (the same
# law as worklog.md, work/ and the build trees). These paths stay local-only.
# gitignore never untracks: the curated files already promoted per wave (e.g.
# docs/evidence/campaign014's tracked subset, evidence/s207/s208/s232 in
# S234-2/S234-3) remain tracked; new wave evidence keeps its deliberate
# per-wave promotion (evidence/s2xx registered in PATH_OWNERSHIP).
# =============================================================================
/CAMPAIGN_STATE.md
/CONT-*.md
/F023_ROOT_CAUSE.md
/PLAYABILITY_REPORT.md
/MessageSchema.java
/current_size_
/gfx_trace.jsonl
/third_party/
/forensic_data/
/reference/
/docs/evidence/campaign014/
"""
lines_s = "".join(f"/evidence/{d}/\n" for d in lines)
section += "# historical pre-S230 evidence dirs carrying untracked run artifacts\n" + lines_s

cur = GITIGNORE.read_text()
if "S235-0 boundary-sweep fix" in cur:
    print("already applied — nothing to do")
else:
    GITIGNORE.write_text(cur.rstrip("\n") + "\n" + section)
    print(f"appended {len(lines)} evidence dirs; "
          f"skipped(fully-local-but-unlisted)={len(skipped)}")
