#!/usr/bin/env python3
"""Policy-validator law test (CONSTITUTION_V2 §172.5, #587 R32).

Builds a synthetic minimal git repo in a temp dir and asserts:
  POSITIVE — legitimate runtime source, pinned reference, fixture, and a
             canonical evidence image pass with zero violations.
  NEGATIVE — each forbidden artifact class is REJECTED:
             root stray, python bytecode, DB WAL, oversized new image outside
             canonical evidence, machine path in a maintained area, unknown
             top-level directory, >100 KiB duplicate, contradictory evidence.
Exit 0 = law holds.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

VALIDATOR = Path(__file__).resolve().parents[1] / "tools" / "policy_validator.py"
PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d494844520000000100000001080200000090775"
    "3de0000000c4944415408d763f8cfc00000030101")
# 1.2 MiB oversized PNG: real header + filler so size gate triggers
BIG_PNG = PNG_1PX + b"\x00" * (1200 * 1024)


def sh(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def build_repo() -> Path:
    repo = Path(tempfile.mkdtemp(prefix="policy_law_"))
    sh(repo, "init", "-q")
    sh(repo, "config", "user.email", "t@t")
    sh(repo, "config", "user.name", "t")
    for d in ("miniandroid/src", "tests", "fixtures", "docs/evidence/canonical",
              "docs/upstream/androidx/compose/1.6.7", "canonical", "scripts/release",
              "evidence", "tools", ".github/workflows"):
        (repo / d).mkdir(parents=True, exist_ok=True)
    # POSITIVE set: legitimate files
    (repo / "README.md").write_text("# ok\n")
    (repo / "LICENSE").write_text("MIT\n")
    (repo / "CONSTITUTION_V2.md").write_text("# C\n")
    (repo / ".gitignore").write_text(".cache/\n")
    (repo / "root_registry.json").write_text("[]\n")
    (repo / "miniandroid/src/engine.cpp").write_text("int main(){return 0;}\n")
    (repo / "tests/law_test.cpp").write_text("int t(){return 1;}\n")
    (repo / "fixtures/input.txt").write_text("fixture input\n")
    (repo / "docs/evidence/canonical/demo.png").write_bytes(PNG_1PX)
    (repo / "docs/upstream/androidx/compose/1.6.7/MANIFEST.json").write_text("{}\n")
    (repo / "canonical/registry.json").write_text("{}\n")
    (repo / "scripts/release/package.sh").write_text("#!/bin/sh\necho hi\n")
    sh(repo, "add", "-A")
    sh(repo, "commit", "-qm", "positive")
    return repo


def run_validator(repo):
    env = dict(os.environ, MINIANDROID_REPO_ROOT=str(repo))
    return subprocess.run([sys.executable, str(VALIDATOR), "check"], capture_output=True,
                          text=True, env=env, timeout=120)


def write_and_commit(repo, relpath, data):
    p = repo / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        p.write_text(data)
    else:
        p.write_bytes(data)
    sh(repo, "add", "-A")
    sh(repo, "commit", "-qm", f"add {relpath}")


NEGATIVES = [
    ("ROOT_STRAY", "session_out1.txt", "session output",
     "ROOT_LAW"),
    ("PYC", "miniandroid/src/__pycache__/x.pyc", b"\x00bytecode",
     "FORBIDDEN_CLASS"),
    ("WAL", "evidence/legacy/data.sqlite3-wal", b"\x00wal",
     "FORBIDDEN_CLASS"),
    ("BIG_IMAGE_NONCANONICAL", "evidence/wave999/screenshot.png", BIG_PNG,
     "IMAGE_OVER_1MB"),
    ("MACHINE_PATH_MAINTAINED", "tools/newtool.py", 'P = "/home/z/my-project/x"\n',
     "MACHINE_PATH_MAINTAINED"),
    ("UNKNOWN_TOPLEVEL", "w999_dump/out.json", "{}\n",
     "TOP_LEVEL_OWNERSHIP"),
    ("DUPLICATE_OVER_100KB", "evidence/wave999/frame_dump.bin", b"D" * 150 * 1024,
     "DUPLICATE_OVER_100KB"),
    ("CONTRADICTORY_EVIDENCE", "evidence/w998/run1/trace_summary.json",
     json.dumps({"frame_analysis": {"app_draw_ops": 0, "verdict": "REAL_APP_CONTENT"}}),
     "CONTRADICTORY_EVIDENCE"),
]


def main():
    failures = []
    # PASS 1: positive baseline
    repo = build_repo()
    r = run_validator(repo)
    if r.returncode != 0:
        failures.append(f"POSITIVE baseline rejected: {r.stdout[-400:]}")
    # PASS 2: each negative is rejected (fresh repo per case; baseline stays green)
    for name, rel, data, expect in NEGATIVES:
        repo = build_repo()
        write_and_commit(repo, rel, data)
        if name == "DUPLICATE_OVER_100KB":
            write_and_commit(repo, "evidence/wave999/frame_dump_copy.bin", data)
        r = run_validator(repo)
        if expect not in r.stdout:
            failures.append(f"NEGATIVE {name}: expected {expect} in validator output, got:\n{r.stdout[-400:]}")
        if r.returncode == 0:
            failures.append(f"NEGATIVE {name}: validator exited 0 (violation not enforced)")
    if failures:
        print("POLICY LAW TEST: FAIL")
        for f in failures:
            print(" -", f)
        sys.exit(1)
    print("POLICY LAW TEST: PASS — positive baseline accepted; all 8 negative classes rejected")


if __name__ == "__main__":
    main()
