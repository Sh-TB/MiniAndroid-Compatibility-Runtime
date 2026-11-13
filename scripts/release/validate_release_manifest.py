#!/usr/bin/env python3
"""S214-WP1 release-manifest validator (#587 comment 6853939129).

Enforces the HARD RELEASE GATE on docs/releases/RELEASE_MANIFEST.json:
  * required_platforms must enumerate every mandated platform (linux-x64, windows-x64)
    with status PASS / BLOCKED / NOT_BUILT
  * a normal/stable/cross-platform release_class with ANY required platform != PASS
    FAILS (no silent downgrade)
  * any non-PASS platform must carry a non-empty blocker + diagnosis reference
  * PASS platforms must reference a real artifact with a 64-hex sha256 and byte size
  * NOT_BUILT is only valid for a draft/preview class, never for stable

Exit 0 = manifest satisfies the S214 gate; exit 1 = the exact violations print.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("MINIANDROID_REPO_ROOT")
            or Path(__file__).resolve().parents[2])
MANIFEST = ROOT / "docs" / "releases" / "RELEASE_MANIFEST.json"
MANDATED = ("linux-x64", "windows-x64")
VALID_STATUS = ("PASS", "BLOCKED", "NOT_BUILT")
STABLE_CLASSES = ("stable", "normal", "cross-platform", "cross_platform", "complete")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")

ARTIFACTS_DIR = ROOT / "docs" / "releases"


def validate(doc):
    violations = []
    rc = doc.get("release_class", {})
    rc_value = str(rc.get("value", "")).strip().lower()
    platforms = doc.get("required_platforms")
    if not isinstance(platforms, dict) or not platforms:
        return ["required_platforms missing or empty — the S214 schema requires every "
                "mandated platform with status PASS/BLOCKED/NOT_BUILT"]
    for p in MANDATED:
        if p not in platforms:
            violations.append(f"required platform '{p}' not enumerated in required_platforms")
    for name, info in sorted(platforms.items()):
        status = info.get("status")
        if status not in VALID_STATUS:
            violations.append(f"{name}: status '{status}' not in {VALID_STATUS}")
            continue
        if status == "PASS":
            art = info.get("artifact")
            sha = info.get("sha256")
            if not art:
                violations.append(f"{name}: PASS without artifact name")
            elif not SHA_RE.match(str(sha or "")):
                violations.append(f"{name}: PASS without valid 64-hex sha256")
            if not isinstance(info.get("bytes"), int) or info["bytes"] <= 0:
                violations.append(f"{name}: PASS without byte size")
        else:
            if not str(info.get("blocker", "")).strip():
                violations.append(f"{name}: {status} without an exact blocker statement")
            if not str(info.get("diagnosis", "")).strip():
                violations.append(f"{name}: {status} without a diagnosis/provenance reference")
        if status == "NOT_BUILT" and rc_value in STABLE_CLASSES:
            violations.append(f"{name}: NOT_BUILT is not publishable for a stable-class release")
    if rc_value in STABLE_CLASSES:
        bad = [p for p, i in platforms.items() if i.get("status") != "PASS"]
        if bad:
            violations.append(
                "no-silent-downgrade violation: release_class '%s' with non-PASS required "
                "platforms %s — a normal/stable release requires ALL mandated platforms PASS; "
                "reclassify as linux-only-preview/experimental with the gap prominent, or "
                "attach the missing artifact" % (rc_value, bad))
    else:
        if "linux-only" not in rc_value and "preview" not in rc_value and "experimental" not in rc_value:
            violations.append(f"release_class '{rc_value}' is neither stable nor an explicit "
                              "linux-only-preview/experimental classification")
        missing = [p for p, i in platforms.items()
                   if p not in ("linux-x64",) and i.get("status") != "PASS"]
        note = str(rc.get("note", "")) + str(rc.get("windows_status", ""))
        if missing and "windows" not in note.lower():
            violations.append("release_class note must state the missing platform prominently "
                              "(windows) when the class is linux-only-preview")
    return violations


def main():
    if not MANIFEST.exists():
        print("FAIL RELEASE_MANIFEST_MISSING", MANIFEST)
        return 1
    doc = json.loads(MANIFEST.read_text())
    violations = validate(doc)
    for v in violations:
        print("FAIL", v)
    if violations:
        print("RELEASE_MANIFEST_GATE: FAIL (%d violation(s))" % len(violations))
        return 1
    print("RELEASE_MANIFEST_GATE: PASS — class '%s'; platforms: %s"
          % (doc.get("release_class", {}).get("value"),
             ", ".join("%s=%s" % (k, v.get("status")) for k, v in
                       sorted(doc.get("required_platforms", {}).items()))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
