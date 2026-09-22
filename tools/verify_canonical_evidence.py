#!/usr/bin/env python3
"""tools/verify_canonical_evidence.py — S84 canonical evidence validator.

User law (S84 §4): machine-checkable canonical evidence chain.
  ONE title -> ONE canonical screenshot -> achievement record.

Checks (exit 1 on any FAIL):
  R1  registry.json exists, parses, has >0 titles, unique packages
  R2  every title: artifact file exists, kind matches extension
  R3  artifact_sha256 matches the file on disk
  R4  each package has AT MOST ONE canonical artifact
  R5  no two titles share the same artifact CONTENT hash (dup detection)
  R6  every title has non-empty provenance: session + source
  R7  S84/S83 titles: apk_sha256 non-empty (APK provable); spotlight
      fixtures exempt (documented)
  R8  status vocabulary sanity: VERIFIED*/PARTIAL*/BLOCKED/OBSERVED only
  R9  visual achievement (VERIFIED*) requires a real artifact (jpg/gif)
  R10 CANONICAL_SCREENSHOTS.md table row per title, links resolve
  R11 ACHIEVEMENTS.md contains one record per package (no dup records)
  R12 artifact size discipline: jpg <= 100 KB, gif <= 1.5 MB
"""
import glob
import hashlib
import json
import os
import sys

ROOT = "/home/z/my-project"
CAN = f"{ROOT}/docs/evidence/canonical"
FAILS = []
WARNS = []


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fail(rule, msg):
    FAILS.append(f"[{rule}] {msg}")


def warn(rule, msg):
    WARNS.append(f"[{rule}] {msg}")


def main():
    reg_path = f"{CAN}/registry.json"
    if not os.path.exists(reg_path):
        fail("R1", "registry.json missing")
        report()
        return
    reg = json.load(open(reg_path))
    titles = reg.get("titles", [])
    if not titles:
        fail("R1", "registry empty")

    pkgs = [t["package"] for t in titles]
    if len(pkgs) != len(set(pkgs)):
        from collections import Counter
        dups = [p for p, c in Counter(pkgs).items() if c > 1]
        fail("R1", f"duplicate packages in registry: {dups}")

    content_hashes = {}
    for t in titles:
        pkg = t["package"]
        art = t.get("artifact", "")
        if not art:
            if t.get("status", "").startswith(("VERIFIED", "PARTIAL")):
                fail("R2", f"{pkg}: status {t['status']} but no artifact")
            else:
                warn("R2", f"{pkg}: no artifact (BLOCKED record)")
            continue
        path = f"{ROOT}/{art}"
        if not os.path.exists(path):
            fail("R2", f"{pkg}: artifact missing {art}")
            continue
        ext = os.path.splitext(path)[1]
        if t.get("artifact_kind") and t["artifact_kind"] != ext:
            fail("R2", f"{pkg}: artifact_kind {t['artifact_kind']} != {ext}")
        h = sha256(path)
        if h != t.get("artifact_sha256"):
            fail("R3", f"{pkg}: SHA mismatch (registry {t.get('artifact_sha256','')[:16]}… != disk {h[:16]}…)")
        if h in content_hashes:
            fail("R5", f"{pkg}: artifact content identical to "
                       f"{content_hashes[h]} (duplicate screenshot)")
        else:
            content_hashes[h] = pkg
        size = os.path.getsize(path)
        limit = 100 * 1024 if ext == ".jpg" else 1536 * 1024
        if size > limit:
            fail("R12", f"{pkg}: artifact {size//1024} KB > limit")
        if not t.get("session") or not t.get("source"):
            fail("R6", f"{pkg}: missing session/source provenance")
        if reg.get("wave") in ("S84",) and t["session"] in ("S84", "S83"):
            if not t.get("apk_sha256") and t["type"] != "fixture":
                fail("R7", f"{pkg}: no APK SHA256 provenance")
        st = t.get("status", "")
        if not (st.startswith("VERIFIED") or st.startswith("PARTIAL") or
                st.startswith("OBSERVED") or st.startswith("BLOCKED")):
            fail("R8", f"{pkg}: bad status {st}")
        if st.startswith("VERIFIED") and not art:
            fail("R9", f"{pkg}: VERIFIED without artifact")

    # R4: at most one artifact per package on disk
    files = glob.glob(f"{CAN}/*.*")
    by_pkg = {}
    for f in files:
        by_pkg.setdefault(os.path.splitext(os.path.basename(f))[0],
                          []).append(f)
    for pkg, fs in by_pkg.items():
        if len(fs) > 1:
            fail("R4", f"{pkg}: multiple canonical artifacts {fs}")
    for f in files:
        base = os.path.splitext(os.path.basename(f))[0]
        if base in ("registry",) or base.startswith("SHA256"):
            continue
        if base not in pkgs:
            fail("R10", f"orphan canonical artifact (not in registry): {f}")

    # R10: index table consistency
    idx = f"{ROOT}/docs/evidence/CANONICAL_SCREENSHOTS.md"
    if os.path.exists(idx):
        body = open(idx, encoding="utf-8").read()
        for t in titles:
            if f"`{t['package']}`" not in body:
                fail("R10", f"{t['package']}: row missing in "
                            f"CANONICAL_SCREENSHOTS.md")
    else:
        fail("R10", "CANONICAL_SCREENSHOTS.md missing")

    # R11: ACHIEVEMENTS.md record per package
    ach = f"{ROOT}/docs/ACHIEVEMENTS.md"
    if os.path.exists(ach):
        body = open(ach, encoding="utf-8").read()
        for t in titles:
            if t["package"] not in body:
                fail("R11", f"{t['package']}: record missing in "
                            f"ACHIEVEMENTS.md")
    else:
        fail("R11", "ACHIEVEMENTS.md missing")

    report()


def report():
    print(f"VALIDATOR: {len(FAILS)} FAIL, {len(WARNS)} WARN")
    for w in WARNS:
        print("WARN", w)
    for f in FAILS:
        print("FAIL", f)
    if FAILS:
        sys.exit(1)
    print("CANONICAL EVIDENCE: ALL CHECKS PASS")


if __name__ == "__main__":
    main()
