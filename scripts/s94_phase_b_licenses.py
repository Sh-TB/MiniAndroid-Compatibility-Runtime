#!/usr/bin/env python3
"""S94 Phase B: LICENSE mining.

For every VERIFIED repository, fetch the license file from
raw.githubusercontent.com at the EXACT HEAD SHA pinned in Phase A
(provenance-pinned evidence, not "whatever main is today").

Output: run/s94/source_mining/license_map.json
"""
import concurrent.futures as cf
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("/home/z/my-project/run/s94/source_mining")
CANDIDATES = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.txt",
              "COPYING.LESSER", "LICENSE-MIT", "NOTICE", "LICENSES/BSD-3-Clause"]
UA = {"User-Agent": "miniandroid-s94-miner/1.0"}


def fetch_raw(repo, sha, path, timeout=15):
    url = f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None


def classify_spdx(text: str) -> str:
    head = text[:2048].lower()
    if "apache license" in head and "version 2.0" in head:
        return "Apache-2.0"
    if "boost software license" in head:
        return "BSL-1.0"
    if "gnu lesser general public license" in head:
        return "LGPL-2.1-or-later" if "2.1" in head else "LGPL"
    if "gnu general public license" in head:
        return "GPL-2.0-or-later" if "version 2" in head and "version 3" not in head else "GPL-3.0"
    if "mozilla public license" in head:
        return "MPL-2.0"
    if "permission is hereby granted, free of charge" in head and "mit" in head:
        return "MIT"
    if "permission is hereby granted, free of charge" in head:
        return "MIT-style"
    if "redistribution and use in source and binary forms" in head:
        n = head.count("redistribution and use in source and binary forms")
        return f"BSD-style({n}-clause-candidate)"
    if "zlib" in head:
        return "Zlib"
    if "unicode" in head and "license" in head:
        return "Unicode-3.0/ICU-style"
    return "UNCLASSIFIED"


def mine(rec):
    if rec["status"] != "VERIFIED":
        rec["license"] = "UNKNOWN"
        rec["license_source"] = "NOT_FETCHED_OFF_GITHUB" if rec["status"] == "OFF_GITHUB" else "REPO_UNVERIFIED"
        return rec
    repo, sha = rec["repository"], rec["head_sha"]
    found = None
    for cand in CANDIDATES:
        data = fetch_raw(repo, sha, cand)
        if data is None or len(data) < 40:
            continue
        text = data.decode("utf-8", "replace")
        # skip placeholder files that are not actual licenses
        if "spdx-license-identifier" in text[:100].lower() and len(data) < 60:
            continue
        found = {"file": cand, "bytes": len(data),
                 "sha256": hashlib.sha256(data).hexdigest(),
                 "spdx": classify_spdx(text)}
        break
    if found is None:
        rec["license"] = "NO_LICENSE_FILE_IN_STANDARD_PATHS"
        rec["license_source"] = f"checked={','.join(CANDIDATES)}"
        rec["reuse_class"] = "REFERENCE_ONLY_UNTIL_LICENSE_CLARIFIED"
        return rec
    rec["license"] = found["spdx"]
    rec["license_evidence"] = found
    rec["license_class"] = license_class(found["spdx"])
    rec["reuse_class"] = reuse_class(found["spdx"])
    return rec


def license_class(spdx):
    if spdx.startswith("Apache") or spdx.startswith("MIT") or spdx.startswith("BSD") \
       or spdx.startswith("Zlib") or spdx.startswith("BSL") or spdx.startswith("Unicode"):
        return "PERMISSIVE"
    if spdx.startswith("LGPL"):
        return "WEAK_COPYLEFT"
    if spdx.startswith("GPL") or spdx.startswith("MPL"):
        return "COPYLEFT_LIKE"
    return "UNCLASSIFIED"


def reuse_class(spdx):
    if license_class(spdx) == "PERMISSIVE":
        return "SAFE_PORT_WITH_ATTRIBUTION"
    if license_class(spdx) == "WEAK_COPYLEFT":
        return "COPY_REQUIRES_NOTICE"
    return "REFERENCE_ONLY"


def main():
    doc = json.loads((OUT / "repositories.json").read_text())
    recs = doc["repositories"]
    with cf.ThreadPoolExecutor(max_workers=10) as ex:
        recs = list(ex.map(mine, recs))
    doc["repositories"] = recs
    doc["license_mined_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    counts = {}
    for r in recs:
        counts[r.get("license", "?")] = counts.get(r.get("license", "?"), 0) + 1
    doc["license_distribution"] = counts
    (OUT / "repositories.json").write_text(json.dumps(doc, indent=1))
    lm = {r["id"]: {"repository": r["repository"], "status": r["status"],
                    "license": r.get("license"), "class": r.get("license_class"),
                    "reuse": r.get("reuse_class"),
                    "evidence": r.get("license_evidence")}
          for r in recs}
    (OUT / "license_map.json").write_text(json.dumps(lm, indent=1))
    print(json.dumps(counts, indent=1))
    miss = [r["repository"] for r in recs if r.get("license", "").startswith("NO_LICENSE")]
    print("no-license-file:", miss)


if __name__ == "__main__":
    sys.exit(main())
