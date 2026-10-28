#!/usr/bin/env python3
"""cont49_roster.py — «چند قطار» CONT-49 wave roster builder.
Enumerate every APK on disk, extract pkg via androguard (manifest parse),
match against plugins/apps.jsonl, and emit the train roster for pkgs whose
registry row is NOT_TESTED (or has no execution evidence yet).
Output: run/cont49/roster.tsv  (label<TAB>apk_path)"""
import os, sys, json, glob
from loguru import logger
logger.remove()

from androguard.core.bytecodes.apk import APK

BASE = "/home/z/my-project"

# --- on-disk APK inventory (all known dirs, deduped by content sha) ---
patterns = [
    f"{BASE}/upload/*.apk",
    f"{BASE}/upload/canonical_apks/*.apk",
    f"{BASE}/upload/cont73_apks/*.apk",
    f"{BASE}/upload/foundation_apks/*.apk",
    f"{BASE}/upload/cont50_apks/*.apk",
]
apks = []
for pat in patterns:
    apks.extend(glob.glob(pat))
# dedup by sha256
seen_sha, inventory = set(), []
for a in sorted(set(apks)):
    import hashlib
    h = hashlib.sha256(open(a, "rb").read()).hexdigest()
    if h in seen_sha:
        continue
    seen_sha.add(h)
    inventory.append(a)
print(f"on-disk unique APKs: {len(inventory)}")

# --- registry state by pkg ---
rows, seen_pkg = [], set()
for ln in open(f"{BASE}/plugins/apps.jsonl"):
    ln = ln.strip()
    if not ln:
        continue
    r = json.loads(ln)
    p = str(r.get("pkg") or "?")
    if p in seen_pkg:
        continue
    seen_pkg.add(p)
    rows.append(r)
state = {str(r.get("pkg")): str(r.get("load") or "NOT_TESTED") for r in rows}

# --- pkg extraction per APK ---
os.makedirs(f"{BASE}/run/cont49", exist_ok=True)
out = open(f"{BASE}/run/cont49/roster.tsv", "w")
apks_has_evidence = 0
candidates = []
for a in inventory:
    try:
        p = APK(a).get_package()
    except Exception as e:
        print(f"PARSE-FAIL|{os.path.basename(a)}|{type(e).__name__}")
        continue
    st = state.get(p)
    if st in ("VERIFIED", "OBSERVED", "PARTIAL", "TESTED"):
        apks_has_evidence += 1
        continue
    if not p:
        # empty pkg (manifest parse gap): honest filename fallback label;
        # apply-time will match by report.md APK path, not pkg.
        label = "fn_" + os.path.basename(a).replace(".", "_").replace("-", "_")[:40]
        candidates.append((label, a, p or "(none)", st or "NOT_TESTED"))
        out.write(f"{label}\t{a}\n")
        continue
    label = p.replace(".", "_")[:40]
    candidates.append((label, a, p, st or "NOT_TESTED"))
    out.write(f"{label}\t{a}\n")
out.close()

print(f"already-evidenced APKs skipped: {apks_has_evidence}")
print(f"train candidates (no evidence): {len(candidates)}")
for label, a, p, st in candidates:
    print(f"  {label}|{os.path.basename(a)}|{st}")
print("ROSTER-DONE")
